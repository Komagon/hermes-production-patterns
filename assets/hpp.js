/* Hermes Production Patterns — V2 交互层
 * 目标: <10KB 原生 JS,零依赖,零外部请求 (任务书 §39)
 * 1) 图谱 hover: 焦点节点高亮 + 关联弱高亮 + 其余暗化 (§11)
 * 2) Pattern Explorer: 分类过滤 + 关键词搜索 (§25)
 * 3) 滚动淡入: IntersectionObserver 一次性 (§33)
 * 兼容 Material instant navigation: 全部逻辑挂在 DOMContentLoaded + $document$
 */
(function () {
  "use strict";
  document.documentElement.classList.add("hpp-js");

  function initGraphs(root) {
    (root || document).querySelectorAll(".hpp-graph[data-edges]").forEach(function (svg) {
      if (svg.dataset.hppReady) return;
      svg.dataset.hppReady = "1";
      var adj = {}; // id -> Set(ids)
      svg.querySelectorAll(".hpp-node").forEach(function (n) {
        adj[n.dataset.id] = new Set();
      });
      svg.querySelectorAll(".hpp-edge").forEach(function (e) {
        var a = e.dataset.from, b = e.dataset.to;
        if (adj[a]) adj[a].add(b);
        if (adj[b]) adj[b].add(a);
      });
      function focus(nodeEl) {
        var id = nodeEl.dataset.id;
        svg.classList.add("is-focusing");
        svg.querySelectorAll(".hpp-node").forEach(function (n) {
          n.classList.toggle("is-focus", n === nodeEl);
          n.classList.toggle("is-lit", adj[id].has(n.dataset.id));
        });
        svg.querySelectorAll(".hpp-edge").forEach(function (e) {
          e.classList.toggle("is-lit", e.dataset.from === id || e.dataset.to === id);
        });
      }
      function clear() {
        svg.classList.remove("is-focusing");
        svg.querySelectorAll(".is-focus,.is-lit").forEach(function (el) {
          el.classList.remove("is-focus");
          el.classList.remove("is-lit");
        });
      }
      svg.querySelectorAll(".hpp-node").forEach(function (n) {
        n.addEventListener("mouseenter", function () { focus(n); });
        n.addEventListener("mouseleave", clear);
        n.addEventListener("focus", function () { focus(n); });
        n.addEventListener("blur", clear);
      });
      svg.addEventListener("mouseleave", clear);
    });
  }

  function initExplorer(root) {
    var page = (root || document).querySelector("[data-hpp-explorer]");
    if (!page) return;
    var cards = Array.prototype.slice.call(page.querySelectorAll(".hpp-pcard"));
    var buttons = Array.prototype.slice.call(page.querySelectorAll(".hpp-filters [data-filter]"));
    var box = page.querySelector(".hpp-searchbox");
    var state = { cat: "all", q: "" };
    var count = page.querySelector("[data-hpp-count]");

    function apply() {
      var shown = 0;
      cards.forEach(function (c) {
        var okCat = state.cat === "all" || c.dataset.cat === state.cat;
        var okQ =
          !state.q ||
          (c.dataset.search || "").indexOf(state.q) !== -1;
        var vis = okCat && okQ;
        c.classList.toggle("hpp-hidden", !vis);
        if (vis) shown++;
      });
      if (count) count.textContent = shown;
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        state.cat = b.dataset.filter;
        buttons.forEach(function (o) {
          o.classList.toggle("is-active", o === b);
        });
        apply();
      });
    });
    if (box) {
      box.addEventListener("input", function () {
        state.q = box.value.trim().toLowerCase();
        apply();
      });
    }
    apply(); /* 初始同步 SHOWN 计数 */
    var act = page.querySelector(".hpp-filters .is-active") ||
      page.querySelector('.hpp-filters [data-filter="all"]');
    if (act) act.classList.add("is-active");
  }

  function initReveal() {
    if (!("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add("hpp-in");
            io.unobserve(en.target); /* 一次性,不循环 (§33) */
          }
        });
      },
      { threshold: 0, rootMargin: "0px 0px -6% 0px" }
    );
    document.querySelectorAll(".hpp-reveal:not(.hpp-in)").forEach(function (el) {
      io.observe(el);
    });
    /* 兜底: 1.5s 后强制全部显形 —— 任何环境(IO 异常/打印/快照抓取)
       都不允许内容停留在隐藏态。动画只是锦上添花,不是显示开关。 */
    setTimeout(function () {
      document.querySelectorAll(".hpp-reveal:not(.hpp-in)").forEach(function (el) {
        el.classList.add("hpp-in");
        io.unobserve(el);
      });
    }, 1500);
  }

  function initConsole(root) {
    var console = (root || document).querySelector('.hpp-console');
    if (!console || console.dataset.hppReady) return;
    console.dataset.hppReady = '1';
    var states = [
      { el: '#hpc-scheduler', texts: ['INITIALIZING', 'ACTIVE'], delay: 0 },
      { el: '#hpc-maker', texts: ['QUEUED', 'EXECUTING', 'COMPLETE'], delay: 400 },
      { el: '#hpc-checker', texts: ['WAITING', 'VALIDATING', 'PASSED'], delay: 800 },
      { el: '#hpc-state', texts: ['PENDING', 'WRITING', 'SYNCHRONIZED'], delay: 1200 }
    ];
    states.forEach(function(s) {
      var el = console.querySelector(s.el);
      if (!el) return;
      el.textContent = s.texts[0];
      el.style.opacity = '0.5';
      s.texts.forEach(function(text, i) {
        if (i === 0) return;
        setTimeout(function() {
          el.textContent = text;
          el.style.opacity = i === s.texts.length - 1 ? '1' : '0.7';
          if (i === s.texts.length - 1) {
            el.style.color = 'var(--hpp-accent-primary)';
          }
        }, s.delay + i * 600);
      });
    });
  }


  function boot(root) {
    initGraphs(root);
    initExplorer(root);
    initReveal();
    initConsole(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { boot(); });
  } else {
    boot();
  }
  /* Material instant-navigation: 每次换页重新初始化新 DOM */
  document$.subscribe(function (doc) { boot(doc); });
})();
