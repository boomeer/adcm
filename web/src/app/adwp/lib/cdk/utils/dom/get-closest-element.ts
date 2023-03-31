export function getClosestElement(element: Element, selector: string): Element | null {
  const closest = Element.prototype.closest;

  if (closest) {
    return closest.call(element, selector);
  }

  const matchesSelector =
    Element.prototype.matches || (Element.prototype as any).msMatchesSelector;

  do {
    if (matchesSelector.call(element, selector)) {
      return element;
    }

    (element as Element | null) = element.parentElement;
  } while (element !== null);

  return null;
}