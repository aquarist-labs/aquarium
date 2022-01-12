/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import {
  AbstractControl,
  AsyncValidatorFn,
  FormArray,
  FormGroup,
  ValidationErrors,
  ValidatorFn
} from '@angular/forms';
import * as _ from 'lodash';
import { Observable, of, timer } from 'rxjs';
import { map, switchMapTo, take } from 'rxjs/operators';
import validator from 'validator';

import { Constraint } from '~/app/shared/models/constraint.type';
import { ConstraintService } from '~/app/shared/services/constraint.service';

const isEmptyInputValue = (value: any): boolean => _.isNull(value) || value.length === 0;

export type ApiFn = (value: any) => Observable<boolean>;

/**
 * Get the data on the top form.
 *
 * @param control The control to start searching for the top most form.
 * @return The raw values of the top form.
 */
const getFormValues = (control: AbstractControl): any[] => {
  if (!control) {
    return [];
  }
  let parent: FormGroup | FormArray | null = control.parent;
  while (parent?.parent) {
    parent = parent.parent;
  }
  return parent ? parent.getRawValue() : [];
};

export class GlassValidators {
  /**
   * Validator to check if the input is a valid IP-address or FQDN.
   *
   * @returns a validator function. The function returns the error `hostAddress` if the
   * validation fails, otherwise `null`.
   */
  static hostAddress(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const err = { hostAddress: true };
      if (_.isEmpty(control.value)) {
        return null;
      }
      const s: string = control.value;
      const fields = s.split(':');
      const host: string = fields[0];
      if (fields.length > 2) {
        return err;
      } else if (fields.length === 2 && !validator.isInt(fields[1])) {
        return err;
      }

      const valid =
        // eslint-disable-next-line @typescript-eslint/naming-convention
        validator.isIP(host) || validator.isFQDN(host, { require_tld: false });
      return !valid ? err : null;
    };
  }

  /**
   * Validator to check if a specific value is unique compared to the already existing
   * elements.
   *
   * @param api The API service function to call and check whether the component value
   *  is unique or not. The function must return `true` if the value exists, otherwise
   *  `false`.
   * @param thisArg `this` object for the service call.
   * @param interval Service call delay. It's useful to prevent the validation on any
   *  keystroke.
   * @returns an async validator function. The function returns the error `notUnique`
   *  if the validation failed, otherwise `null`.
   */
  static unique(api: ApiFn, thisArg: any = null, interval: number = 500): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      if (_.isEmpty(control.value)) {
        return of(null);
      }
      return timer(interval).pipe(
        switchMapTo(api.call(thisArg, control.value)),
        map((resp: boolean) => {
          if (!resp) {
            return null;
          } else {
            return { notUnique: true };
          }
        }),
        take(1)
      );
    };
  }

  /**
   * Validator that requires controls to fulfill the specified constraint.
   * If the constraint is fullfilled, the 'required' validation error will
   * be returned, otherwise null.
   *
   * @param constraint The constraint to process.
   * @returns a validator function.
   */
  static requiredIf(constraint: Constraint): ValidatorFn {
    let hasSubscribed = false;
    const props = ConstraintService.getProps(constraint);
    return (control: AbstractControl): ValidationErrors | null => {
      if (!hasSubscribed && control.parent) {
        props.forEach((key) => {
          control.parent!.get(key)!.valueChanges.subscribe(() => {
            control.updateValueAndValidity({ emitEvent: false });
          });
        });
        hasSubscribed = true;
      }
      const result = ConstraintService.test(constraint, getFormValues(control));
      if (!result) {
        return null;
      }
      return isEmptyInputValue(control.value) ? { required: true } : null;
    };
  }

  /**
   * Validator that requires controls to fulfill the specified constraint.
   * If the constraint is falsy, the 'custom' validation error with the
   * specified error message will be returned, otherwise null.
   *
   * @param constraint The constraint to process.
   * @param errorMessage The error message to be return.
   * @returns a validator function.
   */
  static constraint(constraint: Constraint, errorMessage: string): ValidatorFn {
    let hasSubscribed = false;
    const props = ConstraintService.getProps(constraint);
    return (control: AbstractControl): ValidationErrors | null => {
      if (!hasSubscribed && control.parent) {
        props.forEach((key) => {
          control.parent!.get(key)!.valueChanges.subscribe(() => {
            control.updateValueAndValidity({ emitEvent: false });
          });
        });
        hasSubscribed = true;
      }
      const result = ConstraintService.test(constraint, getFormValues(control));
      return !result ? { custom: errorMessage } : null;
    };
  }
}
