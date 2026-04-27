const GITHUB_REPO_API = "https://api.github.com/repos/ByteWorthyLLC/honeypot-med";
const GITHUB_RELEASE_API = `${GITHUB_REPO_API}/releases/latest`;
const RELEASE_ASSET_MATCHERS = {
  "macos-pkg": /-macos\.pkg$/i,
  "macos-tar": /-macos\.tar\.gz$/i,
  "linux-tar": /-linux-.*\.tar\.gz$/i,
  "windows-zip": /-windows-portable\.zip$/i,
  checksums: /SHA256SUMS\.txt$/i,
  manifest: /release-manifest\.json$/i,
};

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

function formatDate(value) {
  if (!value) {
    return "--";
  }
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function findReleaseAsset(release, key) {
  const matcher = RELEASE_ASSET_MATCHERS[key];
  const assets = Array.isArray(release.assets) ? release.assets : [];
  if (!matcher) {
    return null;
  }
  return assets.find((asset) => matcher.test(asset.name || "")) || null;
}

function setReleaseFallback() {
  document.querySelectorAll("[data-release-version]").forEach((node) => {
    node.textContent = "Pending";
  });
  document.querySelectorAll("[data-release-date]").forEach((node) => {
    node.textContent = "--";
  });
  document.querySelectorAll("[data-release-assets-count]").forEach((node) => {
    node.textContent = "0";
  });
  document.querySelectorAll("[data-release-asset-name]").forEach((node) => {
    node.textContent = "Pending tag";
  });
}

async function hydrateReleaseSurface() {
  const versionNodes = Array.from(document.querySelectorAll("[data-release-version]"));
  const assetLinks = Array.from(document.querySelectorAll("[data-release-asset]"));
  const releaseLinks = Array.from(document.querySelectorAll("[data-release-link]"));
  if (!versionNodes.length && !assetLinks.length && !releaseLinks.length) {
    return;
  }

  try {
    const response = await fetch(GITHUB_RELEASE_API, {
      mode: "cors",
      cache: "no-store",
      headers: {
        Accept: "application/vnd.github+json",
      },
    });
    if (!response.ok) {
      throw new Error("Failed to load GitHub release data");
    }
    const release = await response.json();
    const version = release.tag_name || "Pending";
    const published = formatDate(release.published_at);
    const assetCount = Array.isArray(release.assets) ? release.assets.length : 0;
    const releaseUrl = release.html_url || "https://github.com/ByteWorthyLLC/honeypot-med/releases";

    versionNodes.forEach((node) => {
      node.textContent = version;
    });
    document.querySelectorAll("[data-release-date]").forEach((node) => {
      node.textContent = published;
    });
    document.querySelectorAll("[data-release-assets-count]").forEach((node) => {
      node.textContent = formatCompactCount(assetCount);
    });
    releaseLinks.forEach((node) => {
      node.setAttribute("href", releaseUrl);
    });
    assetLinks.forEach((node) => {
      const key = node.getAttribute("data-release-asset") || "";
      const asset = findReleaseAsset(release, key);
      const label = document.querySelector(`[data-release-asset-name="${key}"]`);
      if (!asset) {
        if (label) {
          label.textContent = "Not published in latest tag";
        }
        return;
      }
      node.setAttribute("href", asset.browser_download_url);
      if (label) {
        label.textContent = asset.name;
      }
    });
  } catch (_error) {
    setReleaseFallback();
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

function wireScrollHeader() {
  const header = document.querySelector(".site-header");
  if (!header) return;
  let ticking = false;
  const update = () => {
    header.classList.toggle("scrolled", window.scrollY > 8);
    ticking = false;
  };
  window.addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        requestAnimationFrame(update);
        ticking = true;
      }
    },
    { passive: true }
  );
  update();
}

function wireScrollReveal() {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const targets = document.querySelectorAll(
    ".section, .hero, .page-hero, .trap-lab-hero, .cta-band, .feature-card, .page-card, .copy-card, .story-card, .visual-card, .download-card, .gallery-card, .metric-card, .rune-card, .command-card, .faq-item"
  );
  if (prefersReducedMotion || !("IntersectionObserver" in window)) {
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  targets.forEach((el) => el.setAttribute("data-reveal", ""));
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );
  targets.forEach((el) => io.observe(el));
}

function markCurrentNav() {
  const links = document.querySelectorAll(".site-header .nav a");
  if (!links.length) return;
  const here = window.location.pathname.replace(/\/+$/, "/");
  links.forEach((a) => {
    try {
      const href = new URL(a.href, window.location.origin).pathname.replace(/\/+$/, "/");
      if (href && href !== "/" && here.endsWith(href)) {
        a.setAttribute("aria-current", "page");
      }
    } catch (_e) {
      /* no-op */
    }
  });
}

wireCopyButtons();
wireScrollHeader();
wireScrollReveal();
markCurrentNav();
hydrateRepoPulse();
hydrateReleaseSurface();
