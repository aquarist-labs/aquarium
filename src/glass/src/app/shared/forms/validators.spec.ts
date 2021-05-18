import { fakeAsync, tick } from '@angular/core/testing';
import { AbstractControl, FormControl, FormGroup } from '@angular/forms';
import { of } from 'rxjs';

import { GlassValidators } from '~/app/shared/forms/validators';

describe('GlassValidators', () => {
  let formGroup: FormGroup;

  beforeEach(() => {
    formGroup = new FormGroup({
      x: new FormControl()
    });
  });

  describe('hostAddress', () => {
    let control: AbstractControl | null;

    beforeEach(() => {
      control = formGroup.get('x');
      control?.setValidators(GlassValidators.hostAddress());
    });

    it('should validate addr [1]', () => {
      control?.setValue('foo.local');
      expect(control?.valid).toBeTruthy();
    });

    it('should validate addr [2]', () => {
      control?.setValue('172.160.0.1');
      expect(control?.valid).toBeTruthy();
    });

    it('should validate addr [3]', () => {
      control?.setValue('bar:1337');
      expect(control?.invalid).toBeTruthy();
      expect(control?.errors).toEqual({ hostAddress: true });
    });

    it('should not validate addr [1]', () => {
      control?.setValue('123.456');
      expect(control?.invalid).toBeTruthy();
      expect(control?.errors).toEqual({ hostAddress: true });
    });

    it('should not validate addr [2]', () => {
      control?.setValue('foo.ba_z.com');
      expect(control?.invalid).toBeTruthy();
      expect(control?.errors).toEqual({ hostAddress: true });
    });

    it('should not validate addr [3]', () => {
      control?.setValue('foo:1a');
      expect(control?.invalid).toBeTruthy();
      expect(control?.errors).toEqual({ hostAddress: true });
    });
  });

  describe('unique', () => {
    let control: AbstractControl | null;

    beforeEach(() => {
      control = formGroup.get('x');
      control?.setAsyncValidators(GlassValidators.unique((value) => of(value === 'test_value')));
    });

    it('should not show error for empty input', () => {
      expect(control?.invalid).toBeFalsy();
    });

    it('should not show error for unique input', fakeAsync(() => {
      control?.setValue('test_value_new');
      tick(500);
      expect(control?.invalid).toBeFalsy();
    }));

    it('should show error for input not unique', fakeAsync(() => {
      control?.setValue('test_value');
      tick(500);
      expect(control?.invalid).toBeTruthy();
      expect(control?.errors).toEqual({ notUnique: true });
    }));
  });
});
