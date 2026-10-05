import { APIError, normalizeURL } from './core';

const keepAttributes = new Set(['href', 'src', 'action', 'formaction', 'type', 'name', 'method', 'autocomplete', 'placeholder', 'aria-label', 'aria-hidden', 'title', 'alt', 'hidden', 'contenteditable']);
const urlAttributes = new Set(['href', 'src', 'action', 'formaction']);

export function snapshotHTML(document: Document, pageURL: string): string {
  const clone = document.documentElement.cloneNode(true) as HTMLElement;
  clone.querySelectorAll('script,style,template,noscript,object,embed,base,#nckh-phishing-demo-banner').forEach(node => node.remove());
  for (const element of [clone, ...clone.querySelectorAll('*')]) {
    for (const attribute of [...element.attributes]) {
      if (!keepAttributes.has(attribute.name)) element.removeAttribute(attribute.name);
      else if (urlAttributes.has(attribute.name)) {
        try { element.setAttribute(attribute.name, normalizeURL(attribute.value, pageURL)); }
        catch { element.removeAttribute(attribute.name); }
      }
    }
  }
  const walker = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_COMMENT);
  const removed: Node[] = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    let suppress = node.nodeType === Node.COMMENT_NODE;
    for (let element = node.parentElement; element; element = element.parentElement) {
      const editable = element.getAttribute('contenteditable');
      if (element.tagName === 'TEXTAREA' || element.hasAttribute('hidden') || element.getAttribute('aria-hidden')?.toLowerCase() === 'true' || (editable !== null && editable.toLowerCase() !== 'false')) suppress = true;
      if (element === clone) break;
    }
    if (suppress) removed.push(node);
  }
  removed.forEach(node => node.parentNode?.removeChild(node));
  const html = clone.outerHTML;
  if (html.length > 1_000_000) throw new APIError('snapshot_too_large');
  return html;
}
