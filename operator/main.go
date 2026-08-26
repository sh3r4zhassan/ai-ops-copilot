package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/cache"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
)


var agentURL = getAgentURL()

func getAgentURL() string {
    if v := os.Getenv("AGENT_URL"); v != "" {
        return v
    }
    return "http://localhost:5000/diagnose"
}

var scheme = runtime.NewScheme()

func init() {
	_ = clientgoscheme.AddToScheme(scheme)
	_ = AddToScheme(scheme)
}

type IncidentReconciler struct {
	client.Client
}

type diagnoseRequest struct {
	Question string `json:"question"`
}

type diagnoseResponse struct {
	Answer string `json:"answer"`
}

func askAgent(question string) (string, error) {
	body, _ := json.Marshal(diagnoseRequest{Question: question})
	resp, err := http.Post(agentURL, "application/json", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var out diagnoseResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.Answer, nil
}

func (r *IncidentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	var incident Incident
	if err := r.Get(ctx, req.NamespacedName, &incident); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	switch incident.Status.Phase {
	case "":
		question := fmt.Sprintf(
			"Pod %s in namespace %s: %s",
			incident.Spec.PodName, incident.Spec.Namespace, incident.Spec.Symptom,
		)
		answer, err := askAgent(question)
		if err != nil {
			fmt.Printf("failed to reach agent: %v\n", err)
			return ctrl.Result{}, err
		}
		incident.Status.Diagnosis = answer
		incident.Status.Phase = "Diagnosed"
		if err := r.Status().Update(ctx, &incident); err != nil {
			return ctrl.Result{}, err
		}
		fmt.Printf("Incident %s diagnosed.\n", incident.Name)

	case "Diagnosed":
		if incident.Spec.Approved {
			pod := &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{Name: incident.Spec.PodName, Namespace: incident.Spec.Namespace},
			}
			if err := r.Delete(ctx, pod); err != nil {
				return ctrl.Result{}, err
			}
			incident.Status.Phase = "Resolved"
			if err := r.Status().Update(ctx, &incident); err != nil {
				return ctrl.Result{}, err
			}
			fmt.Printf("Incident %s resolved: pod %s deleted after approval.\n", incident.Name, incident.Spec.PodName)
		}
	}

	return ctrl.Result{}, nil
}

func main() {
	ctrl.SetLogger(zap.New(zap.UseDevMode(true)))
	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
    		Scheme: scheme,
    		Cache: cache.Options{
        		DefaultNamespaces: map[string]cache.Config{
            			"default": {},
        		},
    		},
	})
	if err != nil {
		fmt.Printf("failed to start manager: %v\n", err)
		os.Exit(1)
	}

	err = ctrl.NewControllerManagedBy(mgr).
		For(&Incident{}).
		Complete(&IncidentReconciler{Client: mgr.GetClient()})
	if err != nil {
		fmt.Printf("failed to build controller: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("starting incident operator...")
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		fmt.Printf("manager exited with error: %v\n", err)
		os.Exit(1)
	}
}
