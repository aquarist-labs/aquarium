import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import * as _ from 'lodash';
import validator from 'validator';

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
}
