import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { NetworkingStepComponent } from '~/app/pages/install-wizard-page/steps/networking-step/networking-step.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('NetworkingStepComponent', () => {
  let component: NetworkingStepComponent;
  let fixture: ComponentFixture<NetworkingStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, PagesModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkingStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
