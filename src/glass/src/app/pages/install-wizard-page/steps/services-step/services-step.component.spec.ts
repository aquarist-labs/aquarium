import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { ServicesStepComponent } from '~/app/pages/install-wizard-page/steps/services-step/services-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('ServicesStepComponent', () => {
  let component: ServicesStepComponent;
  let fixture: ComponentFixture<ServicesStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        PagesModule,
        NoopAnimationsModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ServicesStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
