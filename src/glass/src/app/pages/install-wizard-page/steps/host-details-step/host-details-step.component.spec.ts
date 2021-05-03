import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { HostDetailsStepComponent } from '~/app/pages/install-wizard-page/steps/host-details-step/host-details-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('HostDetailsStepComponent', () => {
  let component: HostDetailsStepComponent;
  let fixture: ComponentFixture<HostDetailsStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, PagesModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostDetailsStepComponent);
    component = fixture.componentInstance;
    component.config = { fields: [] };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
