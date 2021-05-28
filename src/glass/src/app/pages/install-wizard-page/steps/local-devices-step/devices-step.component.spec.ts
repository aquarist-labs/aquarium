import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { LocalDevicesStepComponent } from '~/app/pages/install-wizard-page/steps/local-devices-step/devices-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('LocalDevicesStepComponent', () => {
  let component: LocalDevicesStepComponent;
  let fixture: ComponentFixture<LocalDevicesStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        PagesModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LocalDevicesStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
