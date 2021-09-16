import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { InstallJoinWizardPageComponent } from '~/app/pages/install-wizard/install-join-wizard-page/install-join-wizard-page.component';
import { PagesModule } from '~/app/pages/pages.module';

describe('InstallJoinWizardPageComponent', () => {
  let component: InstallJoinWizardPageComponent;
  let fixture: ComponentFixture<InstallJoinWizardPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        PagesModule,
        RouterTestingModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallJoinWizardPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
