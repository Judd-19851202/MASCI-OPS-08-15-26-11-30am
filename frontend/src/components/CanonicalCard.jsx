import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { AppIcon } from "@/components/icons/AppIcon";

const SIZE_CLASS_MAP = {
  feature: "wp17-card-surface--feature",
  default: "wp17-card-surface--default",
  compact: "wp17-card-surface--compact",
};

function resolveRoot(element, to, href, disabled) {
  if (disabled) return "div";
  if (element === "button") return "button";
  if (href) return "a";
  if (to) return Link;
  return "div";
}

export function CanonicalCard({
  to,
  href,
  target,
  rel,
  element,
  type = "button",
  onClick,
  icon,
  tone = "slate",
  appearance = "default",
  size = "default",
  eyebrow,
  badge,
  title,
  titleSuffix = null,
  description,
  listItems = [],
  ctaLabel = "Open",
  ctaIcon,
  footerSlot = null,
  children,
  disabled = false,
  disabledLabel = "Locked",
  className,
  contentClassName,
  testId,
  ...props
}) {
  const Root = resolveRoot(element, to, href, disabled);
  const interactive = Boolean((to || href || element === "button") && !disabled);
  const resolvedCtaIcon = ctaIcon || (href ? ExternalLink : ArrowRight);
  const rootProps = {
    className: cn(
      "wp17-card-surface",
      `wp17-tone--${tone}`,
      `wp17-card-surface--${appearance}`,
      SIZE_CLASS_MAP[size] || SIZE_CLASS_MAP.default,
      interactive && "wp17-card-surface--interactive",
      disabled && "wp17-card-surface--disabled",
      className,
    ),
    "data-testid": testId,
    onClick,
    ...props,
  };

  if (Root === Link) {
    rootProps.to = to;
  } else if (Root === "a") {
    rootProps.href = href;
    if (target) rootProps.target = target;
    if (rel) rootProps.rel = rel;
  } else if (Root === "button") {
    rootProps.type = type;
  }

  if (disabled) {
    rootProps["aria-disabled"] = "true";
  }

  return (
    <Root {...rootProps}>
      <span className="wp17-card-surface__accent" aria-hidden="true" />

      <div className="wp17-card-surface__head">
        {icon ? (
          <span className="wp17-card-surface__icon" data-testid={testId ? `${testId}-icon` : undefined}>
            <AppIcon icon={icon} size={size === "compact" ? "sm" : "md"} tone="inverse" />
          </span>
        ) : <span />}

        {badge || eyebrow ? (
          badge || <span className="wp17-card-badge" data-testid={testId ? `${testId}-badge` : undefined}>{eyebrow}</span>
        ) : null}
      </div>

      <div className={cn("wp17-card-surface__content", contentClassName)}>
        <div className="wp17-card-surface__title-row">
          <h3 className="wp17-card-surface__title" data-testid={testId ? `${testId}-title` : undefined}>{title}</h3>
          {titleSuffix}
        </div>

        {description ? (
          <p className="wp17-card-surface__description" data-testid={testId ? `${testId}-description` : undefined}>
            {description}
          </p>
        ) : null}

        {listItems.length > 0 ? (
          <ul className="wp17-card-surface__list" data-testid={testId ? `${testId}-list` : undefined}>
            {listItems.map((item) => (
              <li key={item} className="wp17-card-surface__list-item">
                <span className="wp17-card-surface__list-dot" aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {children}
      </div>

      {(footerSlot || interactive || disabled) ? (
        <div className="wp17-card-surface__footer" data-testid={testId ? `${testId}-footer` : undefined}>
          {footerSlot || (
            <>
              <span className="wp17-card-surface__cta">{disabled ? disabledLabel : ctaLabel}</span>
              {!disabled ? <AppIcon icon={resolvedCtaIcon} size="sm" className="wp17-card-surface__cta-icon" /> : null}
            </>
          )}
        </div>
      ) : null}
    </Root>
  );
}

export default CanonicalCard;