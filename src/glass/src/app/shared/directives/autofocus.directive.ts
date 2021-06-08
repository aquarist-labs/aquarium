import { AfterViewInit, Directive, ElementRef, Input } from '@angular/core';
import _ from 'lodash';

@Directive({
  selector: '[autofocus]' // eslint-disable-line
})
export class AutofocusDirective implements AfterViewInit {
  @Input()
  public set autofocus(condition: any) {
    this.focus =
      condition !== false &&
      condition !== 'false' &&
      condition !== 0 &&
      condition !== '0' &&
      condition !== null &&
      condition !== 'null' &&
      condition !== undefined &&
      condition !== 'undefined';
  }

  private focus = true;

  constructor(private elementRef: ElementRef) {}

  ngAfterViewInit() {
    const el: HTMLInputElement = this.elementRef.nativeElement;
    if (this.focus && _.isFunction(el.focus)) {
      setTimeout(() => el.focus());
    }
  }
}
