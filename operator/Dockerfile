FROM golang:1.26 AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o incident-operator .

FROM gcr.io/distroless/static-debian12
COPY --from=builder /build/incident-operator /incident-operator
ENTRYPOINT ["/incident-operator"]
