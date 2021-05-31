import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { HostnameStepComponent } from '~/app/pages/install-wizard/steps/hostname-step/hostname-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('HostnameStepComponent', () => {
  let component: HostnameStepComponent;
  let fixture: ComponentFixture<HostnameStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        PagesModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostnameStepComponent);
    component = fixture.componentInstance;
    component.config = { fields: [] };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
