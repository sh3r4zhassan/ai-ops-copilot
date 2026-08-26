package main

import (
	"os"
	"net/http"
	"context"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"
)

var clientset *kubernetes.Clientset

type PodStatusInput struct {
	Namespace string `json:"namespace" jsonschema:"the Kubernetes namespace to list pods from"`
}

func restartCount(p corev1.Pod) int32 {
	var total int32
	for _, cs := range p.Status.ContainerStatuses {
		total += cs.RestartCount
	}
	return total
}

func getPodStatus(ctx context.Context, req *mcp.CallToolRequest, in PodStatusInput) (*mcp.CallToolResult, any, error) {
	ns := in.Namespace
	if ns == "" {
		ns = "default"
	}

	pods, err := clientset.CoreV1().Pods(ns).List(ctx, metav1.ListOptions{})
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: fmt.Sprintf("error listing pods: %v", err)}},
		}, nil, nil
	}

	var lines []string
	for _, p := range pods.Items {
		lines = append(lines, fmt.Sprintf("%s\t%s\trestarts=%d", p.Name, p.Status.Phase, restartCount(p)))
	}
	if len(lines) == 0 {
		lines = append(lines, fmt.Sprintf("no pods found in namespace %q", ns))
	}

	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: strings.Join(lines, "\n")}},
	}, nil, nil
}

func main() {
	config, err := rest.InClusterConfig()
	if err != nil {
    		kubeconfig := os.Getenv("KUBECONFIG")
    		if kubeconfig == "" {
        		kubeconfig = filepath.Join(homedir.HomeDir(), ".kube", "config")
    		}
    		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
    		if err != nil {
        		log.Fatalf("failed to load any kubeconfig: %v", err)
    		}
	}
	clientset, err = kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("failed to create k8s client: %v", err)
	}

	server := mcp.NewServer(&mcp.Implementation{Name: "k8s-mcp-server", Version: "v0.1.0"}, nil)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_pod_status",
		Description: "List pods and their status/restart counts in a given Kubernetes namespace",
	}, getPodStatus)

	handler := mcp.NewStreamableHTTPHandler(func(r *http.Request) *mcp.Server {
    		return server
	}, nil)

	log.Println("k8s-mcp-server listening on :8080")
	if err := http.ListenAndServe(":8080", handler); err != nil {
    		log.Fatalf("server failed: %v", err)
	}
}
