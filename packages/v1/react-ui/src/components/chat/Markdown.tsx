import { FC, memo } from "react";
import ReactMarkdown, { Options, Components } from "react-markdown";
import { CodeBlock } from "./CodeBlock";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";

const defaultComponents: Components = {
  a({ children, node, ...props }) {
    return (
      <a
        className="copilotKitMarkdownElement"
        {...props}
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    );
  },
  // @ts-expect-error -- inline
  code({ children, className, inline, node, ...props }) {
    if (Array.isArray(children) && children.length) {
      if (children[0] == "▍") {
        return (
          <span
            style={{
              animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
              marginTop: "0.25rem",
            }}
          >
            ▍
          </span>
        );
      }

      children[0] = (children?.[0] as string).replace("`▍`", "▍");
    }

    const match = /language-(\w+)/.exec(className || "");

    // Detect inline code: if it has a language class or contains newlines, it's likely a code block
    // Otherwise, treat it as inline code
    const hasLanguage = match && match[1];
    const content = String(children);
    const hasNewlines = content.includes("\n");
    const isInline = !hasLanguage && !hasNewlines;

    if (isInline) {
      return (
        <code
          className={`copilotKitMarkdownElement copilotKitInlineCode ${className || ""}`}
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <CodeBlock
        key={Math.random()}
        language={(match && match[1]) || ""}
        value={String(children).replace(/\n$/, "")}
        {...props}
      />
    );
  },
  h1: ({ children, node, ...props }) => (
    <h1 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, node, ...props }) => (
    <h2 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, node, ...props }) => (
    <h3 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h3>
  ),
  h4: ({ children, node, ...props }) => (
    <h4 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h4>
  ),
  h5: ({ children, node, ...props }) => (
    <h5 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h5>
  ),
  h6: ({ children, node, ...props }) => (
    <h6 className="copilotKitMarkdownElement" {...props}>
      {children}
    </h6>
  ),
  p: ({ children, node, ...props }) => (
    <p className="copilotKitMarkdownElement" {...props}>
      {children}
    </p>
  ),
  pre: ({ children, node, ...props }) => (
    <pre className="copilotKitMarkdownElement" {...props}>
      {children}
    </pre>
  ),
  blockquote: ({ children, node, ...props }) => (
    <blockquote className="copilotKitMarkdownElement" {...props}>
      {children}
    </blockquote>
  ),
  ul: ({ children, node, ...props }) => (
    <ul className="copilotKitMarkdownElement" {...props}>
      {children}
    </ul>
  ),
  li: ({ children, node, ...props }) => (
    <li className="copilotKitMarkdownElement" {...props}>
      {children}
    </li>
  ),
};

const MemoizedReactMarkdown: FC<Options> = memo(
  ReactMarkdown,
  (prevProps, nextProps) =>
    prevProps.children === nextProps.children &&
    prevProps.components === nextProps.components,
);

type MarkdownProps = {
  content: string;
  components?: Components;
};

export const Markdown = ({ content, components }: MarkdownProps) => {
  return (
    <div className="copilotKitMarkdown">
      <MemoizedReactMarkdown
        components={{ ...defaultComponents, ...components }}
        remarkPlugins={[
          remarkGfm,
          [remarkMath, { singleDollarTextMath: false }],
        ]}
        rehypePlugins={[rehypeRaw]}
      >
        {content}
      </MemoizedReactMarkdown>
    </div>
  );
};
