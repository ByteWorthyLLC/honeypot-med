const GITHUB_REPO_API = "https://api.github.com/repos/ByteWorthyLLC/honeypot-med";

function formatCompactCount(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "--";
  }
  return new Intl.NumberFormat("en-US", {
    notation: numeric >= 1000 ? "compact" : "standard",
    maximumFractionDigits: numeric >= 1000 ? 1 : 0,
  }).format(numeric);
}

async function hydrateRepoPulse() {
  const metricNodes = Array.from(document.querySelectorAll("[data-repo-metric]"));
  const pushedNodes = Array.from(document.querySelectorAll("[data-repo-pushed]"));
  if (!metricNodes.length && !pushedNodes.length) {
    return;
  }

  try {
    const response = await fetch(GITHUB_REPO_API, {
      mode: "cors",
      cache: "no-store",
      headers: {
        Accept: "application/vnd.github+json",
      },
    });
    if (!response.ok) {
      throw new Error("Failed to load GitHub repo pulse");
    }
    const repo = await response.json();
    metricNodes.forEach((node) => {
      const key = node.getAttribute("data-repo-metric");
      node.textContent = formatCompactCount(repo[key]);
    });
    pushedNodes.forEach((node) => {
      const value = repo.pushed_at ? new Date(repo.pushed_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      }) : "--";
      node.textContent = value;
    });
  } catch (_error) {
    metricNodes.forEach((node) => {
      node.textContent = "--";
    });
    pushedNodes.forEach((node) => {
      node.textContent = "--";
    });
  }
}

function wireCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.getAttribute("data-copy") || "";
      try {
        await navigator.clipboard.writeText(value);
        const original = button.textContent;
        button.textContent = "Copied";
        setTimeout(() => {
          button.textContent = original;
        }, 1200);
      } catch (_error) {
        button.textContent = "Copy failed";
      }
    });
  });
}

document.querySelectorAll("[data-year]").forEach((node) => {
  node.textContent = String(new Date().getFullYear());
});

wireCopyButtons();
hydrateRepoPulse();
