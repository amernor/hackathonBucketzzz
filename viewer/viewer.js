let viewer;

Autodesk.Viewing.Initializer({
  env: "AutodeskProduction2", api: "streamingV2",
  getAccessToken: cb => fetch("/api/token").then(r => r.json())
    .then(t => cb(t.access_token, t.expires_in)),
}, () => {
  viewer = new Autodesk.Viewing.GuiViewer3D(document.getElementById("v"));
  viewer.start();
  Autodesk.Viewing.Document.load("urn:" + URN, doc => {
    viewer.loadDocumentNode(doc, doc.getRoot().getDefaultGeometry());
  }, err => console.error("load failed", err));
});
