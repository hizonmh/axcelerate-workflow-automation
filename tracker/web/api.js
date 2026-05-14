// Tiny fetch wrapper for the FastAPI backend. Loaded before any JSX file so
// the React app can call `API.list()`, `API.bulkPatch(...)`, etc.

(function () {
  async function json(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const r = await fetch(path, opts);
    if (!r.ok) {
      let detail = `${r.status} ${r.statusText}`;
      try {
        const j = await r.json();
        if (j.detail) detail = j.detail;
      } catch (_) { /* not json */ }
      throw new Error(detail);
    }
    return r.json();
  }

  window.API = {
    meta:    ()        => json("GET",   "/api/meta"),
    list:    ()        => json("GET",   "/api/transactions"),
    patch:   (id, b)   => json("PATCH", `/api/transactions/${id}`, b),
    bulkPatch: (ids, fields) => json("POST", "/api/transactions/bulk", { ids, ...fields }),
    prepareUpload: (id, b)   => json("POST", `/api/transactions/${id}/prepare-upload`, b),
    upload:  (inst)    => json("POST",  `/api/upload/${inst}`),

    importFiles: async (files) => {
      const fd = new FormData();
      for (const f of files) fd.append("files", f);
      const r = await fetch("/api/import", { method: "POST", body: fd });
      if (!r.ok) {
        let detail = `${r.status} ${r.statusText}`;
        try { const j = await r.json(); if (j.detail) detail = j.detail; } catch (_) {}
        throw new Error(detail);
      }
      return r.json();
    },
  };
})();
