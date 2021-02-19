import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { AbstractControl, FormGroup } from '@angular/forms';
import * as _ from 'lodash';

@Component({
  selector: 'glass-submit-button',
  templateUrl: './submit-button.component.html',
  styleUrls: ['./submit-button.component.scss']
})
export class SubmitButtonComponent implements OnInit {
  @Input()
  form?: FormGroup;

  @Output()
  buttonClick = new EventEmitter<Event>();

  constructor() {}

  ngOnInit(): void {}

  onSubmit(event: Event) {
    if (this.form && this.form.invalid) {
      if (this.form instanceof AbstractControl) {
        // Process all invalid controls and update them to draw the
        // as invalid.
        _.forEach<Record<string, AbstractControl>>(
          this.form.controls,
          (control: AbstractControl, key: string) => {
            if (control.invalid) {
              control.markAllAsTouched();
            }
          }
        );
      }
      return;
    }
    this.buttonClick.emit(event);
  }
}
