{{- define "weather-mcp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "weather-mcp.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "weather-mcp-%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "weather-mcp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end }}
