import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { NtpStepComponent } from '~/app/pages/install-wizard/steps/ntp-step/ntp-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('NtpStepComponent', () => {
  let component: NtpStepComponent;
  let fixture: ComponentFixture<NtpStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, PagesModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NtpStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
