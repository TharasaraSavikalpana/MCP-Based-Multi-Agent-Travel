import html
import json
import os
from typing import Any, Dict, Generator, List

import gradio as gr
import requests
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
if not BACKEND_URL.startswith(("http://", "https://")):
    BACKEND_URL = f"https://{BACKEND_URL}"


THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ===== CSS RESET & ROOT ===== */
:root {
  --tw-font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --tw-ink: #0f172a;
  --tw-ink-light: #334155;
  --tw-muted: #64748b;
  --tw-subtle: #94a3b8;
  --tw-card: #ffffff;
  --tw-card-glass: rgba(255, 255, 255, 0.92);
  --tw-border: rgba(15, 23, 42, 0.06);
  --tw-border-hover: rgba(15, 23, 42, 0.12);
  --tw-ocean: #0ea5e9;
  --tw-ocean-deep: #0284c7;
  --tw-sky: #38bdf8;
  --tw-mint: #10b981;
  --tw-mint-light: #d1fae5;
  --tw-coral: #f97316;
  --tw-amber: #f59e0b;
  --tw-red: #ef4444;
  --tw-bg: #f8fafc;
  --tw-bg-warm: #fafaf9;
  --tw-hero-grad: linear-gradient(135deg, #0c4a6e 0%, #0369a1 35%, #0e7490 70%, #155e75 100%);
  --tw-radius: 16px;
  --tw-radius-sm: 10px;
  --tw-radius-xs: 6px;
  --tw-shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
  --tw-shadow-md: 0 4px 12px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.02);
  --tw-shadow-lg: 0 12px 32px rgba(0,0,0,0.06), 0 4px 8px rgba(0,0,0,0.03);
  --tw-shadow-xl: 0 20px 50px rgba(0,0,0,0.08);
}

/* ===== GLOBAL RESETS - HIDE GRADIO ===== */
body, .gradio-container {
  font-family: var(--tw-font) !important;
  min-height: 100vh;
  background: var(--tw-bg) !important;
  color: var(--tw-ink);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.gradio-container {
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
}

.main {
  max-width: 1360px !important;
  margin: 0 auto !important;
  padding: 0 24px !important;
}

/* Hide Gradio branding, footers, borders */
footer { display: none !important; }
.gradio-container > .wrap { border: none !important; }
.contain { border: none !important; gap: 0 !important; }
.gap { gap: 16px !important; }
.block { border: none !important; box-shadow: none !important; background: transparent !important; }
.block .wrap { border: none !important; }
.label-wrap { display: none !important; }
.form { border: none !important; background: transparent !important; gap: 12px !important; }
#component-0 { border: none !important; }
.gradio-container .contain > .gap > .block:first-child > .block { border: none !important; }

/* ===== HERO SECTION ===== */
#tw-hero {
  position: relative;
  overflow: hidden;
  padding: 48px 48px 40px;
  border-radius: 0 0 28px 28px;
  color: white;
  background: var(--tw-hero-grad);
  margin-bottom: 28px;
  border: none;
}

#tw-hero::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
  pointer-events: none;
}

#tw-hero::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: 10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 70%);
  pointer-events: none;
}

.tw-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: rgba(255,255,255,0.9);
}

.tw-hero-title {
  font-size: 48px;
  font-weight: 900;
  margin: 0 0 12px;
  letter-spacing: -1.5px;
  line-height: 1.05;
  background: linear-gradient(135deg, #ffffff 0%, #bae6fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tw-hero-desc {
  max-width: 620px;
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: rgba(224,242,254,0.85);
  font-weight: 400;
}

.tw-hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.tw-hero-chip {
  padding: 7px 16px;
  border-radius: var(--tw-radius-sm);
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  transition: all 0.2s ease;
}

.tw-hero-chip:hover {
  background: rgba(255,255,255,0.18);
  transform: translateY(-1px);
}

/* ===== NAVBAR ===== */
#tw-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 48px;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--tw-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.tw-nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 800;
  color: var(--tw-ink);
  letter-spacing: -0.5px;
}

.tw-nav-brand-icon {
  width: 32px;
  height: 32px;
  background: var(--tw-hero-grad);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
}

.tw-nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.tw-nav-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--tw-muted);
  text-decoration: none;
  transition: color 0.2s;
}

.tw-nav-link:hover { color: var(--tw-ink); }

.tw-nav-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  font-size: 11px;
  font-weight: 700;
  color: #047857;
}

.tw-nav-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: tw-pulse-dot 2s infinite;
}

@keyframes tw-pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ===== MAIN LAYOUT ===== */
.tw-main-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  margin-top: 0;
  align-items: start;
}

/* ===== CHAT PANEL ===== */
.panel {
  border-radius: var(--tw-radius) !important;
  border: 1px solid var(--tw-border) !important;
  background: var(--tw-card) !important;
  box-shadow: var(--tw-shadow-md) !important;
  padding: 0 !important;
  overflow: hidden;
}

/* Chatbot container - remove black background */
.chatbot {
  background: var(--tw-bg) !important;
  border: none !important;
}

.chatbot .messages {
  background: var(--tw-bg) !important;
}

.chatbot .message {
  border: none !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
}

.chatbot .user {
  background: linear-gradient(135deg, #0369a1, #0284c7) !important;
  color: white !important;
  border-radius: 16px 16px 4px 16px !important;
  padding: 12px 18px !important;
  max-width: 85% !important;
  box-shadow: 0 4px 12px rgba(3, 105, 161, 0.2) !important;
}

.chatbot .bot {
  background: var(--tw-card) !important;
  color: var(--tw-ink) !important;
  border-radius: 16px 16px 16px 4px !important;
  padding: 16px 20px !important;
  max-width: 95% !important;
  box-shadow: var(--tw-shadow-sm) !important;
  border: 1px solid var(--tw-border) !important;
}

/* Fix empty black space in chatbot */
.chatbot .message-wrap {
  background: var(--tw-bg) !important;
  min-height: 0 !important;
}

div[class*="chatbot"] {
  background: var(--tw-bg) !important;
}

div[class*="message-wrap"], div[data-testid="chatbot"] {
  background: var(--tw-bg) !important;
}

/* ===== TEXT INPUT ===== */
.tw-input-area {
  padding: 16px 20px;
  background: var(--tw-card);
  border-top: 1px solid var(--tw-border);
}

textarea, input[type="text"] {
  border-radius: var(--tw-radius-sm) !important;
  border: 1.5px solid rgba(15, 23, 42, 0.08) !important;
  padding: 14px 16px !important;
  font-size: 14px !important;
  font-family: var(--tw-font) !important;
  background: var(--tw-bg) !important;
  transition: all 0.2s ease !important;
  color: var(--tw-ink) !important;
}

textarea:focus, input[type="text"]:focus {
  border-color: var(--tw-ocean) !important;
  box-shadow: 0 0 0 3px rgba(14,165,233,0.1) !important;
  background: white !important;
}

textarea::placeholder { color: var(--tw-subtle) !important; font-weight: 400 !important; }

/* ===== BUTTONS ===== */
.quick-row {
  padding: 0 20px 12px !important;
}

.quick-row button {
  border-radius: var(--tw-radius-sm) !important;
  min-height: 42px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  border: 1px solid var(--tw-border) !important;
  background: var(--tw-card) !important;
  color: var(--tw-ink-light) !important;
  box-shadow: var(--tw-shadow-sm) !important;
  transition: all 0.2s ease !important;
  font-family: var(--tw-font) !important;
}

.quick-row button:hover {
  transform: translateY(-2px) !important;
  border-color: var(--tw-ocean) !important;
  box-shadow: 0 6px 16px rgba(14,165,233,0.1) !important;
  color: var(--tw-ocean-deep) !important;
}

button.primary, #send-btn {
  min-height: 48px !important;
  border-radius: var(--tw-radius-sm) !important;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  font-family: var(--tw-font) !important;
  box-shadow: 0 8px 24px rgba(2,132,199,0.2) !important;
  transition: all 0.25s ease !important;
  letter-spacing: 0.3px !important;
}

button.primary:hover, #send-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 32px rgba(2,132,199,0.3) !important;
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
}

button.primary:active, #send-btn:active {
  transform: translateY(0) !important;
}

/* ===== ACTIVITY PANEL ===== */
#activity-panel {
  border: 1px solid var(--tw-border);
  background: var(--tw-card);
  border-radius: var(--tw-radius);
  padding: 20px;
  box-shadow: var(--tw-shadow-md);
}

/* Gradio's internal class names vary slightly between releases. These
   stable selectors keep the actual product surface light and full-width. */
#tw-chatbot,
#tw-chatbot > div,
#tw-chatbot [data-testid="chatbot"],
#tw-chatbot .wrap,
#tw-chatbot .message-wrap,
#tw-chatbot .messages {
  background: var(--tw-bg) !important;
  border: none !important;
}

#tw-chatbot .message,
#tw-chatbot [data-testid="bot"],
#tw-chatbot [data-testid="user"] {
  width: 100% !important;
  max-width: 100% !important;
}

#tw-chatbot [data-testid="bot"] {
  background: var(--tw-card) !important;
  color: var(--tw-ink) !important;
  border: 1px solid var(--tw-border) !important;
  border-radius: var(--tw-radius) !important;
  box-shadow: var(--tw-shadow-sm) !important;
}

#tw-chatbot [data-testid="bot"] > div,
#tw-chatbot [data-testid="bot"] .prose,
#tw-chatbot [data-testid="bot"] .markdown {
  width: 100% !important;
  max-width: none !important;
}

.tw-activity-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--tw-border);
}

.tw-activity-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--tw-ink);
  letter-spacing: -0.3px;
}

.tw-activity-icon {
  font-size: 16px;
}

.activity-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  padding: 10px 14px;
  border-radius: var(--tw-radius-sm);
  font-size: 12.5px;
  font-weight: 600;
  transition: all 0.3s ease;
  animation: tw-fadeSlideIn 0.3s ease;
  line-height: 1.4;
}

@keyframes tw-fadeSlideIn {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}

.activity-chip .chip-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.activity-chip.good {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.activity-chip.warn {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.activity-chip.run {
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
  animation: tw-fadeSlideIn 0.3s ease, tw-pulse-border 2s infinite 0.3s;
}

@keyframes tw-pulse-border {
  0%, 100% { border-color: #fde68a; box-shadow: none; }
  50% { border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.08); }
}

.activity-chip.idle {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

/* ===== DEMO PROMPTS SIDEBAR ===== */
.tw-sidebar-section {
  border: 1px solid var(--tw-border);
  background: var(--tw-card);
  border-radius: var(--tw-radius);
  padding: 20px;
  box-shadow: var(--tw-shadow-sm);
  margin-top: 16px;
}

.tw-sidebar-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--tw-ink);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tw-demo-prompt {
  display: block;
  padding: 8px 12px;
  margin: 6px 0;
  border-radius: var(--tw-radius-xs);
  background: var(--tw-bg);
  color: var(--tw-ink-light);
  font-size: 12.5px;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  cursor: default;
  line-height: 1.4;
}

.tw-demo-prompt:hover {
  border-color: var(--tw-border-hover);
  background: #f0f9ff;
}

.tw-demo-prompt code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 11.5px;
}

/* ===== FOOTER ===== */
#tw-footer {
  text-align: center;
  padding: 32px 20px;
  margin-top: 40px;
  border-top: 1px solid var(--tw-border);
  color: var(--tw-subtle);
  font-size: 12px;
  font-weight: 500;
}

#tw-footer a {
  color: var(--tw-ocean);
  text-decoration: none;
  font-weight: 600;
}

/* ===== RESULT CARDS STYLING ===== */

/* Section Headers */
.tw-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--tw-ocean);
}

.tw-section-icon {
  font-size: 20px;
}

.tw-section-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--tw-ink);
  letter-spacing: -0.4px;
}

.tw-section-count {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--tw-muted);
  background: #f1f5f9;
  padding: 3px 10px;
  border-radius: 999px;
}

/* Cards Grid */
.tw-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

/* Hotel Card */
.tw-hotel-card {
  background: var(--tw-card);
  border-radius: var(--tw-radius);
  border: 1px solid var(--tw-border);
  overflow: hidden;
  transition: all 0.3s ease;
  animation: tw-cardFadeIn 0.4s ease;
}

@keyframes tw-cardFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.tw-hotel-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--tw-shadow-lg);
  border-color: rgba(16,185,129,0.2);
}

.tw-card-image {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.tw-card-image-label {
  font-size: 36px;
  opacity: 0.6;
}

.tw-card-body {
  padding: 14px 16px 12px;
}

.tw-hotel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.tw-hotel-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--tw-ink);
  line-height: 1.3;
}

.tw-hotel-rating {
  font-size: 11px;
  color: #f59e0b;
  font-weight: 700;
  white-space: nowrap;
}

.tw-hotel-rating small {
  color: var(--tw-muted);
  font-weight: 600;
}

.tw-hotel-location {
  font-size: 12px;
  color: var(--tw-muted);
  margin-bottom: 10px;
}

.tw-hotel-amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 8px;
}

.tw-amenity-chip {
  font-size: 10px;
  background: #f1f5f9;
  color: #475569;
  padding: 3px 8px;
  border-radius: var(--tw-radius-xs);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.tw-amenity-icon {
  font-size: 11px;
}

.tw-hotel-extras {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}

.tw-info-tag {
  font-size: 10px;
  color: #047857;
  font-weight: 600;
}

.tw-info-popular {
  color: #d97706;
}

.tw-hotel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--tw-border);
}

.tw-avail-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--tw-radius-xs);
}

.tw-avail-high { background: #ecfdf5; color: #047857; }
.tw-avail-low { background: #fffbeb; color: #92400e; }
.tw-avail-none { background: #fef2f2; color: #b91c1c; }

.tw-hotel-price {
  text-align: right;
}

.tw-price-value {
  font-size: 20px;
  font-weight: 800;
  color: var(--tw-ink);
}

.tw-price-unit {
  font-size: 11px;
  color: var(--tw-muted);
  font-weight: 500;
}

.tw-card-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--tw-border);
}

.tw-hotel-id, .tw-flight-id {
  font-size: 10px;
  color: var(--tw-subtle);
}

.tw-hotel-id code, .tw-flight-id code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 9px;
  background: #f1f5f9;
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--tw-muted);
}

.tw-select-btn {
  font-size: 11px;
  font-weight: 700;
  color: var(--tw-ocean);
  cursor: pointer;
  transition: color 0.2s;
}

.tw-select-btn:hover { color: var(--tw-ocean-deep); }

.tw-more-results {
  text-align: center;
  font-size: 12px;
  color: var(--tw-muted);
  padding: 12px;
  font-weight: 500;
  font-style: italic;
}

/* ===== FLIGHT CARDS ===== */
.tw-flight-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.tw-flight-card {
  background: var(--tw-card);
  border-radius: var(--tw-radius);
  border: 1px solid var(--tw-border);
  padding: 16px 20px;
  transition: all 0.3s ease;
  animation: tw-cardFadeIn 0.4s ease;
}

.tw-flight-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--tw-shadow-lg);
  border-color: rgba(14,165,233,0.2);
}

.tw-flight-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tw-flight-airline-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tw-airline-icon {
  font-size: 16px;
  color: var(--tw-ocean);
}

.tw-airline-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--tw-ink);
}

.tw-flight-price-tag {
  text-align: right;
}

.tw-price-amount {
  font-size: 22px;
  font-weight: 800;
  color: var(--tw-ocean-deep);
  display: block;
  line-height: 1;
}

.tw-price-label {
  font-size: 10px;
  color: var(--tw-muted);
  font-weight: 500;
}

.tw-flight-route {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  border: 1px solid var(--tw-border);
  padding: 16px 20px;
  border-radius: var(--tw-radius-sm);
  margin-bottom: 12px;
}

.tw-route-origin, .tw-route-dest {
  text-align: center;
  min-width: 70px;
}

.tw-airport-code {
  font-size: 24px;
  font-weight: 900;
  color: var(--tw-ink);
  letter-spacing: 1px;
  line-height: 1;
}

.tw-city-label {
  font-size: 11px;
  color: var(--tw-muted);
  margin-top: 4px;
  font-weight: 500;
}

.tw-time-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--tw-ink-light);
  margin-top: 6px;
}

.tw-route-connector {
  flex: 1;
  text-align: center;
  padding: 0 12px;
}

.tw-route-line-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.tw-dot {
  width: 6px;
  height: 6px;
  background: var(--tw-ocean);
  border-radius: 50%;
  flex-shrink: 0;
}

.tw-dash-line {
  flex: 1;
  height: 2px;
  background: repeating-linear-gradient(90deg, #cbd5e1 0px, #cbd5e1 4px, transparent 4px, transparent 8px);
  min-width: 20px;
}

.tw-plane-mid {
  font-size: 14px;
  color: var(--tw-ocean);
  margin: 0 4px;
  flex-shrink: 0;
}

.tw-route-type {
  font-size: 10px;
  font-weight: 700;
  color: var(--tw-mint);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 6px;
}

.tw-flight-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--tw-border);
}

.tw-seats-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: var(--tw-radius-xs);
}

.tw-seats-high { background: #ecfdf5; color: #047857; }
.tw-seats-low { background: #fffbeb; color: #92400e; }
.tw-seats-none { background: #fef2f2; color: #b91c1c; }

/* ===== TRIP SUMMARY ===== */
.tw-trip-summary {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 50%, #ecfdf5 100%);
  border: 1px solid rgba(14,165,233,0.15);
  border-radius: var(--tw-radius);
  overflow: hidden;
  margin-top: 16px;
  animation: tw-cardFadeIn 0.5s ease;
}

.tw-summary-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--tw-border);
}

.tw-summary-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--tw-ink);
  letter-spacing: -0.5px;
}

.tw-summary-dest {
  font-size: 14px;
  color: var(--tw-muted);
  font-weight: 500;
  margin-top: 4px;
}

.tw-budget-ok {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  color: #047857;
  background: #ecfdf5;
  padding: 3px 10px;
  border-radius: 999px;
  margin-top: 8px;
}

.tw-budget-over {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  color: #b91c1c;
  background: #fef2f2;
  padding: 3px 10px;
  border-radius: 999px;
  margin-top: 8px;
}

.tw-map-container {
  padding: 0 24px;
  margin: 16px 0;
}

.tw-map-container iframe {
  border-radius: var(--tw-radius-sm);
  border: 1px solid var(--tw-border);
}

.tw-summary-body {
  padding: 16px 24px;
}

.tw-summary-row {
  padding: 12px 0;
  border-bottom: 1px solid var(--tw-border);
}

.tw-summary-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--tw-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tw-summary-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--tw-ink);
  margin-top: 3px;
}

.tw-summary-meta {
  font-size: 12px;
  color: var(--tw-muted);
  margin-top: 3px;
}

.tw-summary-divider {
  height: 1px;
  background: var(--tw-border);
  margin: 4px 0;
}

.tw-summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 4px;
  font-size: 14px;
  font-weight: 700;
  color: var(--tw-ink);
}

.tw-total-price {
  font-size: 26px;
  font-weight: 900;
  color: var(--tw-ocean-deep);
}

.tw-summary-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: rgba(14,165,233,0.04);
  border-top: 1px solid var(--tw-border);
}

.tw-summary-status {
  font-size: 12px;
  font-weight: 700;
  color: #047857;
}

.tw-summary-tip {
  font-size: 11px;
  color: var(--tw-muted);
}

.tw-summary-tip code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 10px;
  background: rgba(0,0,0,0.04);
  padding: 1px 5px;
  border-radius: 3px;
}

/* ===== GROUNDED AI BRIEF ===== */
.tw-ai-brief {
  margin: 0 0 16px;
  padding: 18px 20px;
  border: 1px solid rgba(14,165,233,0.2);
  border-left: 4px solid var(--tw-ocean);
  border-radius: var(--tw-radius-sm);
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 72%);
  box-shadow: var(--tw-shadow-sm);
  animation: tw-cardFadeIn 0.45s ease;
}

.tw-ai-brief-title {
  color: var(--tw-ocean-deep);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.2px;
  margin-bottom: 8px;
}

.tw-ai-brief-body {
  color: var(--tw-ink-light);
  font-size: 13px;
  line-height: 1.65;
  white-space: normal;
}

/* ===== BOOKING RESULT ===== */
.tw-booking-result {
  border-radius: var(--tw-radius);
  padding: 24px;
  max-width: 440px;
  animation: tw-cardFadeIn 0.5s ease;
}

.tw-booking-success {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
  border: 1px solid #a7f3d0;
}

.tw-booking-failed {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
  border: 1px solid #fecaca;
}

.tw-booking-icon {
  font-size: 36px;
  text-align: center;
  margin-bottom: 8px;
}

.tw-booking-status-title {
  font-size: 20px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}

.tw-booking-success .tw-booking-status-title { color: #047857; }
.tw-booking-failed .tw-booking-status-title { color: #b91c1c; }
.tw-booking-failed .tw-booking-reason { text-align: center; color: #7f1d1d; font-size: 13px; }

.tw-confirmation-box {
  text-align: center;
  background: white;
  border: 1px solid #d1fae5;
  border-radius: var(--tw-radius-sm);
  padding: 14px;
  margin-bottom: 16px;
}

.tw-conf-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--tw-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
}

.tw-conf-code {
  font-size: 22px;
  font-weight: 900;
  color: #047857;
  letter-spacing: 2px;
  margin-top: 4px;
  display: block;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.tw-receipt-body {
  padding: 12px 0;
  border-top: 1px solid var(--tw-border);
  border-bottom: 1px solid var(--tw-border);
}

.tw-receipt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.tw-receipt-label {
  font-size: 12px;
  color: var(--tw-muted);
  font-weight: 600;
}

.tw-receipt-value {
  font-size: 13px;
  color: var(--tw-ink);
  font-weight: 700;
}

.tw-receipt-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  font-size: 14px;
  font-weight: 700;
  color: var(--tw-ink);
}

.tw-total-amount {
  font-size: 24px;
  font-weight: 900;
  color: #047857;
}

/* ===== WELCOME / FALLBACK CARD ===== */
.tw-welcome-card {
  background: var(--tw-card);
  border: 1px solid var(--tw-border);
  border-radius: var(--tw-radius);
  overflow: hidden;
  animation: tw-cardFadeIn 0.4s ease;
}

.tw-welcome-header {
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfdf5 100%);
  border-bottom: 1px solid var(--tw-border);
  text-align: center;
}

.tw-welcome-icon { font-size: 32px; margin-bottom: 8px; }
.tw-welcome-title { font-size: 18px; font-weight: 800; color: var(--tw-ink); }
.tw-welcome-subtitle { font-size: 12px; color: var(--tw-muted); margin-top: 4px; font-weight: 500; }

.tw-welcome-body { padding: 20px 24px; }

.tw-welcome-note {
  font-size: 13px;
  color: var(--tw-ink-light);
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--tw-radius-xs);
}

.tw-capability-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.tw-capability {
  padding: 14px;
  border: 1px solid var(--tw-border);
  border-radius: var(--tw-radius-sm);
  background: var(--tw-bg);
  transition: all 0.2s;
}

.tw-capability:hover {
  border-color: var(--tw-ocean);
  background: #f0f9ff;
}

.tw-cap-icon { font-size: 20px; display: block; margin-bottom: 6px; }
.tw-cap-title { font-size: 13px; font-weight: 700; color: var(--tw-ink); display: block; }
.tw-cap-example {
  font-size: 11px; color: var(--tw-muted); font-weight: 500; display: block; margin-top: 4px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

/* ===== CLARIFY & ERROR CARDS ===== */
.tw-clarify-card {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: var(--tw-radius);
  padding: 20px;
  animation: tw-cardFadeIn 0.3s ease;
}

.tw-clarify-title { font-size: 15px; font-weight: 700; color: #0369a1; margin-bottom: 8px; }
.tw-clarify-body { font-size: 13px; color: var(--tw-ink-light); line-height: 1.6; }
.tw-clarify-example { font-size: 12px; color: var(--tw-muted); margin-top: 10px; }
.tw-clarify-example code {
  font-family: 'SF Mono', 'Fira Code', monospace; font-size: 11px;
  background: rgba(0,0,0,0.04); padding: 2px 6px; border-radius: 3px;
}

.tw-error-card {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--tw-radius);
  padding: 16px 20px;
  font-size: 13px;
  color: #991b1b;
  font-weight: 500;
  animation: tw-cardFadeIn 0.3s ease;
}

.tw-notice-card {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--tw-radius);
  padding: 16px 20px;
  margin-top: 8px;
}

.tw-notice-title { font-size: 14px; font-weight: 700; color: #92400e; margin-bottom: 8px; }
.tw-notice-list { margin: 0; padding-left: 16px; font-size: 12px; color: #78350f; }

/* ===== TRAVEL TIP ===== */
.tw-travel-tip {
  background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
  border: 1px solid #fde68a;
  border-radius: var(--tw-radius);
  padding: 16px 20px;
  margin-top: 12px;
  animation: tw-cardFadeIn 0.5s ease;
}

.tw-tip-header { font-size: 14px; font-weight: 700; color: #92400e; margin-bottom: 6px; }
.tw-tip-body { font-size: 13px; color: #78350f; line-height: 1.7; }

/* ===== EMPTY STATE ===== */
.tw-empty-state {
  text-align: center;
  padding: 32px 20px;
  background: var(--tw-bg);
  border: 1px dashed var(--tw-border-hover);
  border-radius: var(--tw-radius);
}

.tw-empty-icon { font-size: 32px; margin-bottom: 8px; opacity: 0.5; }
.tw-empty-text { font-size: 14px; color: var(--tw-ink-light); font-weight: 600; }
.tw-empty-hint { font-size: 12px; color: var(--tw-muted); margin-top: 4px; }

/* ===== MOBILE RESPONSIVE ===== */
@media (max-width: 768px) {
  #tw-hero {
    padding: 28px 20px 24px;
    border-radius: 0 0 20px 20px;
  }

  .tw-hero-title { font-size: 32px; }
  .tw-hero-desc { font-size: 13px; }

  #tw-nav {
    padding: 12px 16px;
  }

  .tw-nav-links { display: none; }

  .tw-main-grid {
    grid-template-columns: 1fr;
  }

  .tw-cards-grid {
    grid-template-columns: 1fr;
  }

  .tw-capability-grid {
    grid-template-columns: 1fr;
  }

  .tw-flight-route {
    padding: 12px;
  }

  .tw-airport-code {
    font-size: 18px;
  }

  .tw-summary-footer {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .tw-hero-title { font-size: 26px; }
  .tw-hero-chips { gap: 6px; }
  .tw-hero-chip { font-size: 10px; padding: 5px 10px; }

  .quick-row {
    flex-direction: column;
  }

  .quick-row button {
    width: 100% !important;
  }
}
"""


def _message_content(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("text", value.get("content", ""))
    if isinstance(value, list):
        value = " ".join(_message_content(item) for item in value)
    return str(value or "").strip()


def _history_for_api(chat_history: Any) -> List[Dict[str, str]]:
    clean_history: List[Dict[str, str]] = []
    if not isinstance(chat_history, list):
        return clean_history

    for item in chat_history[-12:]:
        role = None
        content = None
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
        elif hasattr(item, "role") and hasattr(item, "content"):
            role = item.role
            content = item.content
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            for r, c in [("user", item[0]), ("assistant", item[1])]:
                text = _message_content(c)
                if text:
                    clean_history.append({"role": r, "content": text})
            continue
        else:
            continue

        if role and content:
            role_str = str(role).strip().lower()
            content_str = _message_content(content)
            if role_str in {"user", "assistant", "system"} and content_str:
                clean_history.append({"role": role_str, "content": content_str})

    return clean_history[-10:]


# Activity state icons and labels (using HTML entities for Windows compat)
_ACTIVITY_CONFIG = {
    "ROUTING": {"icon": "&#129504;", "label": "Routing"},
    "SEARCHING": {"icon": "&#128269;", "label": "Searching"},
    "BOOKING": {"icon": "&#128221;", "label": "Booking"},
    "RESPONDING": {"icon": "&#10024;", "label": "Responding"},
    "CLARIFYING": {"icon": "&#10067;", "label": "Clarifying"},
    "IDLE": {"icon": "&#9200;", "label": "Idle"},
}


def _activity_html(events: List[Dict[str, object]]) -> str:
    header = (
        "<div id='activity-panel'>"
        "<div class='tw-activity-header'>"
        "<span class='tw-activity-icon'>&#9889;</span>"
        "<span class='tw-activity-title'>Agent Activity</span>"
        "</div>"
    )

    if not events:
        return (
            header +
            "<span class='activity-chip idle'>"
            "<span class='chip-icon'>&#9200;</span>"
            "Ready &mdash; waiting for your trip request"
            "</span>"
            "</div>"
        )

    chips = []
    for event in events[-8:]:
        status = event.get("status", "IDLE")
        state = str(event.get("state", "STATUS"))
        message = html.escape(str(event.get("message", "")))

        cfg = _ACTIVITY_CONFIG.get(state, {"icon": "&#9679;", "label": state})

        if status == "SUCCEEDED":
            css = "good"
        elif status == "FAILED":
            css = "warn"
        elif status == "INVOKED":
            css = "run"
        else:
            css = "idle"

        chips.append(
            f"<span class='activity-chip {css}'>"
            f"<span class='chip-icon'>{cfg['icon']}</span>"
            f"{cfg['label']}: {message}"
            f"</span>"
        )

    return header + "".join(chips) + "</div>"


def _record_activity(events: List[Dict[str, object]], event: Dict[str, object]) -> None:
    signature = (
        event.get("state"),
        event.get("status"),
        event.get("message"),
    )
    if any(
        (item.get("state"), item.get("status"), item.get("message")) == signature
        for item in events[-8:]
    ):
        return
    events.append(event)


def chat_with_tripweaver(message: str, chat_history: List[Dict[str, str]]) -> Generator:
    message = _message_content(message)
    chat_history = chat_history if isinstance(chat_history, list) else []
    if not message:
        yield chat_history, _activity_html([])
        return

    api_history = _history_for_api(chat_history)
    chat_history = chat_history + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
    events: List[Dict[str, object]] = [{"state": "ROUTING", "message": "Processing your request...", "status": "INVOKED"}]
    yield chat_history, _activity_html(events)

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/stream",
            json={"message": message, "history": api_history},
            stream=True,
            timeout=90,
        )
        if response.status_code >= 400:
            detail = response.text[:600]
            raise RuntimeError(f"{response.status_code} response from backend: {detail}")

        current_event = ""
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line == "":
                continue
            if raw_line.startswith("event:"):
                current_event = raw_line.replace("event:", "", 1).strip()
                continue
            if not raw_line.startswith("data:"):
                continue

            data = json.loads(raw_line.replace("data:", "", 1).strip())
            if current_event == "activity":
                _record_activity(events, data)
            elif current_event == "token":
                chat_history[-1]["content"] += data.get("text", "")
            elif current_event == "error":
                events.append({"state": "RESPONDING", "message": data.get("message"), "status": "FAILED"})
                chat_history[-1]["content"] = data.get("message", "A backend error occurred.")
            elif current_event == "done":
                # Activity events have already streamed in real time. Do not
                # append them again when the completion envelope arrives.
                pass

            yield chat_history, _activity_html(events)
    except Exception as exc:
        events.append({"state": "RESPONDING", "message": "Connection issue.", "status": "FAILED"})
        chat_history[-1]["content"] = (
            "<div class='tw-error-card'>"
            "&#9888; <strong>Connection Error</strong><br>"
            "TripWeaver could not reach the backend service. "
            "Please ensure the FastAPI server is running and try again.<br>"
            f"<small>Details: {html.escape(str(exc))}</small>"
            "</div>"
        )
        yield chat_history, _activity_html(events)


with gr.Blocks(title="TripWeaver | AI Travel Planner") as demo:
    # Navigation Bar
    gr.HTML(
        """
        <nav id="tw-nav">
          <div class="tw-nav-brand">
            <div class="tw-nav-brand-icon">&#9992;</div>
            TripWeaver
          </div>
          <div class="tw-nav-links">
            <span class="tw-nav-link">Hotels</span>
            <span class="tw-nav-link">Flights</span>
            <span class="tw-nav-link">Plan Trip</span>
          </div>
          <div class="tw-nav-status">
            <span class="tw-nav-dot"></span>
            MCP Connected
          </div>
        </nav>
        """
    )

    # Hero Section
    gr.HTML(
        """
        <section id="tw-hero">
          <div class="tw-hero-badge">&#9889; MCP-Powered Multi-Agent Travel Intelligence</div>
          <h1 class="tw-hero-title">TripWeaver</h1>
          <p class="tw-hero-desc">Plan hotels, flights, and bookings through one intelligent workspace. TripWeaver routes each request to specialist AI agents, queries external travel services through MCP servers, and delivers comprehensive travel plans.</p>
          <div class="tw-hero-chips">
            <span class="tw-hero-chip">&#129504; Intent-Routed LangGraph</span>
            <span class="tw-hero-chip">&#127976; Hotel + Flight MCP Servers</span>
            <span class="tw-hero-chip">&#128268; Live Provider + Fallback</span>
            <span class="tw-hero-chip">&#9889; Streaming FastAPI</span>
          </div>
        </section>
        """
    )

    with gr.Row():
        with gr.Column(scale=3, elem_classes=["panel"]):
            chatbot = gr.Chatbot(
                height=520,
                elem_id="tw-chatbot",
                buttons=["copy", "copy_all"],
                label="Travel planning chat",
                sanitize_html=False,
                show_label=False,
            )
            user_input = gr.Textbox(
                placeholder="Where would you like to travel? Try: 'Plan hotel and flight from Colombo to Singapore under $500'",
                label="Your trip request",
                lines=2,
                show_label=False,
            )
            with gr.Row(elem_classes=["quick-row"]):
                btn_hotels = gr.Button("Hotels in Bangkok")
                btn_flights = gr.Button("Flights BOM to DEL")
                btn_plan = gr.Button("Plan Colombo to Singapore")
                btn_list = gr.Button("List all hotels")
            send = gr.Button("Plan My Trip", variant="primary", elem_id="send-btn")

        with gr.Column(scale=1):
            activity = gr.HTML(_activity_html([]), label="Agent activity")
            gr.HTML(
                """
                <div class="tw-sidebar-section">
                  <div class="tw-sidebar-title">&#128161; Quick Start Guide</div>
                  <div class="tw-demo-prompt"><strong>Search Hotels:</strong><br><code>Hotels in Singapore under $200</code></div>
                  <div class="tw-demo-prompt"><strong>Find Flights:</strong><br><code>Flight from Colombo to Bangkok</code></div>
                  <div class="tw-demo-prompt"><strong>Full Trip Plan:</strong><br><code>Plan hotel and flight to Dubai under $600</code></div>
                  <div class="tw-demo-prompt"><strong>Reserve a Hotel:</strong><br><code>Reserve a hotel using its reference and your name</code></div>
                  <div class="tw-demo-prompt"><strong>Reserve a Flight:</strong><br><code>Reserve a flight using its reference and your name</code></div>
                </div>
                """
            )

    # Footer
    gr.HTML(
        """
        <div id="tw-footer">
          <strong>TripWeaver</strong> &mdash; MCP-Based Multi-Agent Travel Intelligence Platform<br>
          Built with LangGraph &middot; FastAPI &middot; Model Context Protocol &middot; Gradio<br>
          <span style="opacity:0.6">&copy; 2025 TripWeaver. All travel data sourced via MCP servers.</span>
        </div>
        """
    )

    send.click(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    user_input.submit(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    btn_hotels.click(lambda: "available hotels in Bangkok", None, user_input)
    btn_flights.click(lambda: "flight from BOM to DEL", None, user_input)
    btn_plan.click(lambda: "Plan hotel and flight from Colombo to Singapore under $500", None, user_input)
    btn_list.click(lambda: "list all hotels", None, user_input)


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.getenv("FRONTEND_HOST", "0.0.0.0"),
        server_port=int(os.getenv("PORT", os.getenv("FRONTEND_PORT", "7860"))),
        css=THEME_CSS,
    )
