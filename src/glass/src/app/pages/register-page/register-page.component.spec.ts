import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateModule } from '@ngx-translate/core';

import { PagesModule } from '~/app/pages/pages.module';
import { RegisterPageComponent } from '~/app/pages/register-page/register-page.component';

describe('RegisterPageComponent', () => {
  let component: RegisterPageComponent;
  let fixture: ComponentFixture<RegisterPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        PagesModule,
        NoopAnimationsModule,
        RouterTestingModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RegisterPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should validate addr [1]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('foo.local');
    expect(control?.valid).toBeTruthy();
  });

  it('should validate addr [2]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('172.160.0.1');
    expect(control?.valid).toBeTruthy();
  });

  it('should validate addr [3]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('bar:1337');
    expect(control?.valid).toBeTruthy();
  });

  it('should not validate addr [1]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should not validate addr [2]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('123.456');
    expect(control?.invalid).toBeTruthy();
    expect(control?.errors).toEqual({ address: true });
  });

  it('should not validate addr [3]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('foo.ba_z.com');
    expect(control?.invalid).toBeTruthy();
    expect(control?.errors).toEqual({ address: true });
  });

  it('should not validate addr [4]', () => {
    const control = component.formGroup.get('address');
    control?.setValue('foo:1a');
    expect(control?.invalid).toBeTruthy();
    expect(control?.errors).toEqual({ address: true });
  });

  it('should validate token [1]', () => {
    const control = component.formGroup.get('token');
    control?.setValue('1234-abCD-9876-FD01');
    expect(control?.valid).toBeTruthy();
  });

  it('should not validate token [1]', () => {
    const control = component.formGroup.get('token');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should not validate token [2]', () => {
    const control = component.formGroup.get('token');
    control?.setValue('1234+abCD-9876-FD01');
    expect(control?.invalid).toBeTruthy();
  });

  it('should not validate token [3]', () => {
    const control = component.formGroup.get('token');
    control?.setValue('foo');
    expect(control?.invalid).toBeTruthy();
    expect(Object.keys(control?.errors as Record<string, any>)).toContain('pattern');
  });
});
