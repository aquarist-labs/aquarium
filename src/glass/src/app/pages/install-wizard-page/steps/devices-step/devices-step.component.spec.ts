import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { DevicesStepComponent } from '~/app/pages/install-wizard-page/steps/devices-step/devices-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('DevicesStepComponent', () => {
  let component: DevicesStepComponent;
  let fixture: ComponentFixture<DevicesStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        PagesModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DevicesStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
