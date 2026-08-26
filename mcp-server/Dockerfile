FROM golang:1.26 AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o k8s-mcp-server .

FROM gcr.io/distroless/static-debian12
COPY --from=builder /build/k8s-mcp-server /k8s-mcp-server
EXPOSE 8080
ENTRYPOINT ["/k8s-mcp-server"]
