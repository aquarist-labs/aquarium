import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { InstallRegisterPageComponent } from '~/app/pages/install-register-page/install-register-page.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('InstallRegisterPageComponent', () => {
  let component: InstallRegisterPageComponent;
  let fixture: ComponentFixture<InstallRegisterPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        PagesModule,
        NoopAnimationsModule,
        RouterTestingModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallRegisterPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not validate address if empty', () => {
    const control = component.formGroup.get('address');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
  });

  it('should not validate port if empty', () => {
    const control = component.formGroup.get('port');
    control?.setValue('');
    expect(control?.errors).toEqual({ required: true });
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
