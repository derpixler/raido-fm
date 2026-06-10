"use client";

import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { CodeBlock } from "@/components/CodeBlock";
import { slugify } from "@/lib/utils";

/** Hast-Knoten rekursiv zu reinem Text (für den Copy-Button) zusammenfügen. */
function nodeToText(node: unknown): string {
  if (!node || typeof node !== "object") return "";
  const n = node as { value?: string; children?: unknown[] };
  if (typeof n.value === "string") return n.value;
  if (Array.isArray(n.children)) return n.children.map(nodeToText).join("");
  return "";
}

function headingId(children: React.ReactNode): string {
  const text = Array.isArray(children)
    ? children.map((c) => (typeof c === "string" ? c : "")).join("")
    : String(children ?? "");
  return slugify(text);
}

const components: Components = {
  // Keine id hier: der umschließende <section>-Wrapper liefert bereits den
  // Scroll-Anker (sonst entstünden doppelte IDs).
  h2: ({ node: _node, children, ...props }) => (
    <h2
      className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl"
      {...props}
    >
      {children}
    </h2>
  ),
  h3: ({ node: _node, children, ...props }) => (
    <h3
      id={headingId(children)}
      className="mt-10 scroll-mt-28 text-xl font-semibold tracking-tight text-foreground"
      {...props}
    >
      {children}
    </h3>
  ),
  p: ({ node: _node, ...props }) => (
    <p className="mt-5 text-base leading-relaxed text-muted" {...props} />
  ),
  a: ({ node: _node, href, children, ...props }) => (
    <a
      href={href}
      target={href?.startsWith("http") ? "_blank" : undefined}
      rel={href?.startsWith("http") ? "noreferrer noopener" : undefined}
      className="font-medium text-primary-glow underline decoration-primary/40 underline-offset-4 transition-colors hover:text-primary hover:decoration-primary"
      {...props}
    >
      {children}
    </a>
  ),
  ul: ({ node: _node, ...props }) => (
    <ul
      className="mt-5 list-disc space-y-2.5 pl-6 text-base text-muted marker:text-primary"
      {...props}
    />
  ),
  ol: ({ node: _node, ...props }) => (
    <ol
      className="mt-5 list-decimal space-y-2.5 pl-6 text-base text-muted marker:text-primary-glow"
      {...props}
    />
  ),
  li: ({ node: _node, children, ...props }) => (
    <li className="pl-1.5 leading-relaxed" {...props}>
      {children}
    </li>
  ),
  img: ({ src, alt }) => (
    <figure className="my-7">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={typeof src === "string" ? src : ""}
        alt={alt ?? ""}
        loading="lazy"
        decoding="async"
        className="w-full rounded-xl border border-border bg-surface object-cover shadow-[0_20px_60px_-20px_rgba(0,0,0,0.8)]"
      />
      {alt ? (
        <figcaption className="mt-3 text-center text-sm text-muted">
          {alt}
        </figcaption>
      ) : null}
    </figure>
  ),
  blockquote: ({ node: _node, ...props }) => (
    <blockquote
      className="my-6 border-l-2 border-primary/60 bg-surface/50 px-5 py-3 text-base italic text-muted/90 [&>p]:mt-0"
      {...props}
    />
  ),
  strong: ({ node: _node, ...props }) => (
    <strong className="font-semibold text-foreground" {...props} />
  ),
  hr: () => <hr className="my-10 border-border" />,
  table: ({ node: _node, ...props }) => (
    <div className="my-6 overflow-x-auto rounded-xl border border-border">
      <table className="w-full border-collapse text-left text-sm" {...props} />
    </div>
  ),
  thead: ({ node: _node, ...props }) => (
    <thead className="bg-surface" {...props} />
  ),
  th: ({ node: _node, ...props }) => (
    <th
      className="border-b border-border px-4 py-3 font-semibold text-foreground"
      {...props}
    />
  ),
  td: ({ node: _node, ...props }) => (
    <td
      className="border-b border-border/60 px-4 py-3 align-top text-muted"
      {...props}
    />
  ),
  pre: ({ node, children }) => {
    const codeNode = (
      node as unknown as { children?: { tagName?: string }[] }
    )?.children?.find((c) => c?.tagName === "code");
    const classNames =
      ((codeNode as { properties?: { className?: unknown } })?.properties
        ?.className as string[] | undefined) ?? [];
    const language = (Array.isArray(classNames) ? classNames : [])
      .map(String)
      .find((c) => c.startsWith("language-"))
      ?.replace("language-", "");
    const rawCode = nodeToText(codeNode).replace(/\n$/, "");
    // ASCII-Diagramme (Box-Zeichen) sind Grafiken, kein Code: ohne Sprach-Label,
    // Copy-Button und (fälschlich auto-erkanntes) Syntax-Highlighting rendern.
    if (/[┌┐└┘├┤┬┴│▲▼◀▶]/.test(rawCode)) {
      return (
        <figure className="my-6 overflow-x-auto rounded-xl border border-border bg-[#0A0A0A] p-4">
          <pre
            aria-label="Diagram"
            className="whitespace-pre font-mono text-sm leading-relaxed text-[#e4e4e7]"
          >
            {rawCode}
          </pre>
        </figure>
      );
    }
    return (
      <CodeBlock rawCode={rawCode} language={language}>
        {children}
      </CodeBlock>
    );
  },
  code: ({
    node: _node,
    className,
    children,
    ...props
  }: ComponentPropsWithoutRef<"code"> & { node?: unknown }) => {
    const isBlock = /\blanguage-|\bhljs\b/.test(className ?? "");
    if (isBlock) {
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        className="rounded-md border border-border bg-surface px-1.5 py-0.5 font-mono text-[0.85em] text-primary-glow"
        {...props}
      >
        {children}
      </code>
    );
  },
};

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[
          [
            rehypeHighlight,
            {
              detect: true,
              ignoreMissing: true,
              // Eingegrenzte Sprachmenge für die Auto-Erkennung sprachloser
              // Blöcke — verhindert Fehlgriffe wie csharp/vbnet/scss.
              subset: [
                "python",
                "yaml",
                "sql",
                "bash",
                "json",
                "dockerfile",
                "ini",
                "http",
                "nginx",
              ],
            },
          ],
        ]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
