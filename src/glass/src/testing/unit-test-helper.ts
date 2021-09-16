import { ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';

export class FixtureHelper {
  fixture: ComponentFixture<any>;

  constructor(fixture: ComponentFixture<any>) {
    this.fixture = fixture;
  }
  /**
   * Expect a list of id elements to be visible or not.
   */
  expectIdElementsVisible(ids: string[], visibility: boolean) {
    ids.forEach((css) => {
      this.expectElementVisible(`#${css}`, visibility);
    });
  }

  /**
   * Expect a specific element to be visible or not.
   */
  expectElementVisible(css: string, visibility: boolean) {
    expect(visibility).toBe(Boolean(this.getElementByCss(css)));
  }

  expectFormFieldToBe(css: string, value: string) {
    const props = this.getElementByCss(css).properties;
    expect(props.value || props.checked.toString()).toBe(value);
  }

  expectTextToBe(css: string, value: string | null) {
    expect(this.getText(css)).toBe(value);
  }

  expectTextsToBe(css: string, value: string[]) {
    expect(this.getTextAll(css)).toEqual(value);
  }

  clickElement(css: string) {
    this.getElementByCss(css).triggerEventHandler('click', null);
    this.fixture.detectChanges();
  }

  selectElement(css: string, value: string) {
    const nativeElement = this.getElementByCss(css).nativeElement;
    nativeElement.value = value;
    nativeElement.dispatchEvent(new Event('change'));
    this.fixture.detectChanges();
  }

  getText(css: string) {
    const e = this.getElementByCss(css);
    return e ? e.nativeElement.textContent.trim() : null;
  }

  getTextAll(css: string) {
    const elements = this.getElementByCssAll(css);
    return elements.map((element) => (element ? element.nativeElement.textContent.trim() : null));
  }

  getElementByCss(css: string) {
    this.fixture.detectChanges();
    return this.fixture.debugElement.query(By.css(css));
  }

  getElementByCssAll(css: string) {
    this.fixture.detectChanges();
    return this.fixture.debugElement.queryAll(By.css(css));
  }
}
