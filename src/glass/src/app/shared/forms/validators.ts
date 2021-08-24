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
import { AbstractControl, AsyncValidatorFn, ValidationErrors, ValidatorFn } from '@angular/forms';
import * as _ from 'lodash';
import { Observable, of, timer } from 'rxjs';
import { map, switchMapTo, take } from 'rxjs/operators';
import validator from 'validator';

const isEmptyInputValue = (value: any): boolean => _.isNull(value) || value.length === 0;

export type ApiFn = (value: any) => Observable<boolean>;

export class GlassValidators {
  /**
   * Validator to check if the input is a valid IP-address or FQDN.
   *
   * @returns a validator function. The function returns the error `hostAddress` if the
   * validation fails, otherwise `null`.
   */
  static hostAddress(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      if (_.isEmpty(control.value)) {
        return null;
      }
      const valid =
        // eslint-disable-next-line @typescript-eslint/naming-convention
        validator.isIP(control.value) || validator.isFQDN(control.value, { require_tld: false });
      return !valid ? { hostAddress: true } : null;
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
   * Validator that requires controls to fulfill the specified condition if
   * the specified constraints matches. If the prerequisites are fulfilled,
   * then the given function is executed and if it succeeds, the 'required'
   * validation error will be returned, otherwise null.
   *
   * @param constraints An object containing the constraints.
   *   To do additional checks rather than checking for equality you can
   *   use the extended syntax:
   *     'field_name': { 'operator': '<OPERATOR>', arg0: '<OPERATOR_ARGUMENT>' }
   *   The following operators are supported:
   *   * truthy
   *   * falsy
   *   * empty
   *   * !empty
   *   * equal
   *   * !equal
   *   * minLength
   *   * maxLength
   *   ### Example
   *   ```typescript
   *   {
   *     'generate_key': true,
   *     'username': 'Max Mustermann'
   *   }
   *   ```
   *   ### Example - Extended prerequisites
   *   ```typescript
   *   {
   *     'generate_key': { 'operator': 'equal', 'arg0': true },
   *     'username': { 'operator': 'minLength', 'arg0': 5 }
   *   }
   *   ```
   *   Only if all constraints are fulfilled, then the validation of the
   *   control will be triggered.
   * @returns a validator function.
   */
  static requiredIf(constraints: Record<any, any>): ValidatorFn {
    let hasSubscribed = false;
    return (control: AbstractControl): ValidationErrors | null => {
      if (!hasSubscribed && control.parent) {
        Object.keys(constraints).forEach((key) => {
          control.parent!.get(key)!.valueChanges.subscribe(() => {
            control.updateValueAndValidity({ emitEvent: false });
          });
        });
        hasSubscribed = true;
      }
      // Check if all prerequisites met.
      if (
        !Object.keys(constraints).every((key) => {
          if (!control.parent) {
            return false;
          }
          let result = false;
          const value = control.parent.get(key)!.value;
          const constraint = constraints[key];
          if (_.isObjectLike(constraint)) {
            switch (constraint.operator) {
              case 'truthy':
                result = _.includes([1, 'true', true, 'yes', 'y'], value);
                break;
              case 'falsy':
                result = _.includes(
                  [0, 'false', false, 'no', 'n', undefined, null, NaN, ''],
                  value
                );
                break;
              case 'empty':
                result = _.isEmpty(value);
                break;
              case '!empty':
                result = !_.isEmpty(value);
                break;
              case 'equal':
                result = value === constraint.arg0;
                break;
              case '!equal':
                result = value !== constraint.arg0;
                break;
              case 'minLength':
                if (_.isString(value)) {
                  result = value.length >= constraint.arg0;
                }
                break;
              case 'maxLength':
                if (_.isString(value)) {
                  result = value.length < constraint.arg0;
                }
                break;
            }
          } else {
            result = value === constraint;
          }
          return result;
        })
      ) {
        return null;
      }
      return isEmptyInputValue(control.value) ? { required: true } : null;
    };
  }
}
