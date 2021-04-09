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
      const errResult = { hostAddress: true };
      const parts = control.value.split(':');
      if (parts.length === 2) {
        if (!validator.isPort(parts[1])) {
          return errResult;
        }
      }
      const valid =
        // eslint-disable-next-line @typescript-eslint/naming-convention
        validator.isIP(parts[0]) || validator.isFQDN(parts[0], { require_tld: false });
      return !valid ? errResult : null;
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
}
