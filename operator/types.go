package main

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

type IncidentSpec struct {
	PodName   string `json:"podName"`
	Namespace string `json:"namespace"`
	Symptom   string `json:"symptom"`
	Approved  bool   `json:"approved"`
}

type IncidentStatus struct {
	Phase     string `json:"phase,omitempty"`
	Diagnosis string `json:"diagnosis,omitempty"`
}

type Incident struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   IncidentSpec   `json:"spec,omitempty"`
	Status IncidentStatus `json:"status,omitempty"`
}

type IncidentList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []Incident `json:"items"`
}

func (in *Incident) DeepCopyInto(out *Incident) {
	*out = *in
	out.ObjectMeta = *in.ObjectMeta.DeepCopy()
}

func (in *Incident) DeepCopy() *Incident {
	out := &Incident{}
	in.DeepCopyInto(out)
	return out
}

func (in *Incident) DeepCopyObject() runtime.Object {
	return in.DeepCopy()
}

func (in *IncidentList) DeepCopyObject() runtime.Object {
	out := &IncidentList{TypeMeta: in.TypeMeta, ListMeta: in.ListMeta}
	if in.Items != nil {
		out.Items = make([]Incident, len(in.Items))
		for i := range in.Items {
			in.Items[i].DeepCopyInto(&out.Items[i])
		}
	}
	return out
}

var GroupVersion = schema.GroupVersion{Group: "aiops.example.com", Version: "v1alpha1"}

var (
	SchemeBuilder = runtime.NewSchemeBuilder(addKnownTypes)
	AddToScheme   = SchemeBuilder.AddToScheme
)

func addKnownTypes(scheme *runtime.Scheme) error {
	scheme.AddKnownTypes(GroupVersion, &Incident{}, &IncidentList{})
	metav1.AddToGroupVersion(scheme, GroupVersion)
	return nil
}
