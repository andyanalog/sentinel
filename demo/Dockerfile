FROM node:20-alpine

WORKDIR /app

# Build context is the repo root (Railway respects dockerfilePath but uses
# the repo root as context by default). The SDK is a `file:../sdk` dep in
# demo/package.json, so both dirs must be present.
COPY sdk /sdk
COPY demo/package.json demo/package-lock.json /app/

# Rewrite the file: path so npm can resolve the SDK from inside the image.
RUN node -e "const p=require('./package.json');p.devDependencies['@sentinel/sdk']='file:/sdk';require('fs').writeFileSync('./package.json',JSON.stringify(p,null,2))" \
    && npm install --no-audit --no-fund

COPY demo/ /app/

ENV PORT=3000
EXPOSE 3000

CMD ["npx", "tsx", "index.ts"]
