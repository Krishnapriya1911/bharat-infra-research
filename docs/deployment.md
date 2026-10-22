# Deploy the research API

The HTTP service is self-contained and uses mock project data. The report-processing pipeline remains an offline workflow; deploying the API does not run it or deploy a trained model.

## Local verification

From the repository root, with the virtual environment active:

```bash
python -m pytest -q
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

In a second terminal:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/projects/bridge-001
curl --fail -X POST http://127.0.0.1:8000/risk/evaluate \
  -H 'Content-Type: application/json' \
  --data-binary @datasets/mock_project.json
```

Interactive documentation is available at `/docs`. `/health` reports the service as a `research-demo`; it does not report data freshness or model quality.

## Docker

```bash
docker build -t bharat-infra-research .
docker run --rm -p 8000:8000 bharat-infra-research
```

The process runs as a non-root user. Set `PORT` if your host requires a different listening port. No cloud keys, database or external AI service is required for this demo API.

## Render

The root `render.yaml` defines one Docker web service on the free plan with `/health` as its health-check path. In your Render account, create a Blueprint from this repository and review the resource configuration before creating it. Hosting is not activated by merely committing the blueprint.

After deployment, use the URL returned by Render to check `/health`, `/docs`, the sample GET endpoint and a sample POST request. Add the URL to the main README only after those checks pass. Review the provider's current free-plan limits before relying on it for an interview demonstration.

This demo has no authentication and must use sample project data. A deployment for private or real project records requires a separate access-control design.
