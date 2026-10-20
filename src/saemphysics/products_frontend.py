"""Original pilot-product landing page with hosted checkout links."""

import html
import re
from urllib.parse import urlsplit


def _policy_url(value: str | None, policy: str) -> str | None:
    if value is None or not value.strip():
        return None
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError(f"Configured {policy} URL must use HTTPS")
    return value.strip()


def _checkout_url(value: str | None, provider: str) -> str | None:
    if value is None or not value.strip():
        return None
    parsed = urlsplit(value.strip())
    allowed_hosts = {
        "razorpay": {"rzp.io", "razorpay.com", "www.razorpay.com"},
        "paypal": {"paypal.com", "www.paypal.com", "paypal.me"},
    }
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_hosts[provider]
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.strip("/")
        or parsed.fragment
    ):
        raise ValueError(f"Configured {provider} checkout URL is invalid")
    return value.strip()


def render_products_page(
    *,
    sales_enabled: bool = False,
    razorpay_payment_url: str | None = None,
    paypal_payment_url: str | None = None,
    seller_name: str | None = None,
    support_email: str | None = None,
    terms_url: str | None = None,
    privacy_url: str | None = None,
    refunds_url: str | None = None,
    notes_reviewed: bool = False,
) -> str:
    razorpay_url = _checkout_url(razorpay_payment_url, "razorpay")
    paypal_url = _checkout_url(paypal_payment_url, "paypal")
    policy_urls = {
        "terms": _policy_url(terms_url, "terms"),
        "privacy": _policy_url(privacy_url, "privacy"),
        "refunds": _policy_url(refunds_url, "refunds"),
    }
    if support_email is not None and not re.fullmatch(
        r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+",
        support_email,
    ):
        raise ValueError("Configured support email is invalid")
    if sales_enabled:
        if razorpay_url is None or paypal_url is None:
            raise ValueError(
                "Paid checkout requires both Razorpay and PayPal payment links"
            )
        if not all(policy_urls.values()):
            raise ValueError(
                "Paid checkout requires HTTPS terms, privacy, and refund policy URLs"
            )
        if (
            not seller_name
            or not seller_name.strip()
            or not support_email
            or not notes_reviewed
        ):
            raise ValueError(
                "Paid checkout requires seller identity, support contact, "
                "and teacher-reviewed product content"
            )

    if sales_enabled:
        checkout = (
            '<a class="button" rel="noopener noreferrer" '
            f'href="{html.escape(razorpay_url, quote=True)}">'
            "India · pay with Razorpay</a>"
            '<a class="button secondary" rel="noopener noreferrer" '
            f'href="{html.escape(paypal_url, quote=True)}">'
            "International · pay with PayPal</a>"
        )
        seller_details = (
            '<div class="seller-details"><p><strong>Seller:</strong> '
            f'{html.escape(seller_name, quote=True)}</p><p><strong>Support:</strong> '
            f'<a href="mailto:{html.escape(support_email, quote=True)}">'
            f'{html.escape(support_email, quote=True)}</a></p><nav aria-label="Purchase policies">'
            + " · ".join(
                f'<a href="{html.escape(policy_url, quote=True)}" '
                f'rel="noopener noreferrer">{label}</a>'
                for label, policy_url in (
                    ("Terms", policy_urls["terms"]),
                    ("Privacy", policy_urls["privacy"]),
                    ("Refunds", policy_urls["refunds"]),
                )
                if policy_url is not None
            )
            + "</nav></div>"
        )
    else:
        checkout = (
            '<p class="status" role="status">Pre-launch preview — checkout is not enabled yet.</p>'
        )
        seller_details = ""

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#10141b">
    <title>SaemPhysics · Original study resources</title>
    <link rel="stylesheet" href="/assets/student.css">
  </head>
  <body>
    <main class="page">
      <header class="topbar">
        <a class="brand" href="/student">SaemPhysics <span>Study resources</span></a>
        <a class="teacher-link" href="https://www.youtube.com/@SaemPhysics"
           target="_blank" rel="noopener noreferrer">Free lessons · YouTube ↗</a>
      </header>
      <section class="welcome">
        <p class="eyebrow">ORIGINAL SAEMPHYSICS MATERIAL</p>
        <h1>Learn the idea. Check the result.</h1>
        <p>Short, teacher-reviewable resources connected to practice and the
           exact SaemPhysics learning tools.</p>
      </section>
      <section class="card" aria-labelledby="starter-pack">
        <p class="eyebrow">FIRST PILOT · PHYSICS NOTES</p>
        <h2 id="starter-pack">Constant Acceleration Starter Notes</h2>
        <p>A concise original study pack covering sign conventions, units,
           the three constant-acceleration equations, worked examples,
           common errors, and self-check exercises with answers.</p>
        <ul>
          <li>One-dimensional motion with constant acceleration</li>
          <li>Worked examples for speeding up and braking</li>
          <li>Three practice questions with reasoned checks</li>
          <li>Clear scope limits and teacher-review status</li>
        </ul>
        <div class="price-grid">
          <div><strong>India pilot suggestion</strong><span>₹99 one-time</span></div>
          <div><strong>International pilot suggestion</strong><span>US$2.99 one-time</span></div>
        </div>
        <p class="fine-print">Suggested test prices only; confirm they match the
           amounts in the hosted checkout before enabling sales. International
           payment methods and currencies depend on provider and buyer eligibility.</p>
        {checkout}
        <p class="fine-print">Initial fulfilment is manual after payment confirmation.
           {("The listed notes have been reviewed by the teacher." if notes_reviewed else "The notes still need the teacher's review before sale.")}</p>
        {seller_details}
      </section>
      <section class="card">
        <p class="eyebrow">FREE TO EXPLORE</p>
        <h2>Try the learning engine</h2>
        <p>Practice a mechanics question or use the exact solver for motion,
           differentiation, definite integrals, and small linear systems.</p>
        <a class="button" href="/student">Open student practice</a>
      </section>
      <footer>
        Original pilot resource · manual delivery · local prototype
        <span><a href="/teacher">Teacher studio</a> · <a href="/">Workbench</a></span>
      </footer>
    </main>
  </body>
</html>"""
