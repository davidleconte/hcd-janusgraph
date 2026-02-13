{{/*
Common labels
*/}}
{{- define "janusgraph-banking.labels" -}}
app.kubernetes.io/part-of: {{ .Chart.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "janusgraph-banking.namespace" -}}
{{ .Values.namespace | default .Release.Namespace }}
{{- end }}
