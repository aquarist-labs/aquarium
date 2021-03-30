import { AbstractControl, FormControl, FormGroup } from '@angular/forms';

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
      expect(control?.valid).toBeTruthy();
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
});
