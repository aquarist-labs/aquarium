import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { RegistrationStepComponent } from '~/app/pages/install-wizard/steps/registration-step/registration-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('RegistrationStepComponent', () => {
  let component: RegistrationStepComponent;
  let fixture: ComponentFixture<RegistrationStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        PagesModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RegistrationStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not validate address if empty', () => {
    const control = component.form?.formGroup?.get('address');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should not validate port if empty', () => {
    const control = component.form?.formGroup?.get('port');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should validate token [1]', () => {
    const control = component.form?.formGroup?.get('token');
    control?.setValue('1234-abCD-9876-FD01');
    expect(control?.valid).toBeTruthy();
  });

  it('should not validate token [1]', () => {
    const control = component.form?.formGroup?.get('token');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should not validate token [2]', () => {
    const control = component.form?.formGroup?.get('token');
    control?.setValue('1234+abCD-9876-FD01');
    expect(control?.invalid).toBeTruthy();
  });

  it('should not validate token [3]', () => {
    const control = component.form?.formGroup?.get('token');
    control?.setValue('foo');
    expect(control?.invalid).toBeTruthy();
    expect(Object.keys(control?.errors as Record<string, any>)).toContain('pattern');
  });
});
