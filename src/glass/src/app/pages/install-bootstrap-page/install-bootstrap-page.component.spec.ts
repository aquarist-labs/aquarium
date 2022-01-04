import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { InstallBootstrapPageComponent } from '~/app/pages/install-bootstrap-page/install-bootstrap-page.component';
import { PagesModule } from '~/app/pages/pages.module';
import { TestingModule } from '~/app/testing.module';

describe('InstallBootstrapPageComponent', () => {
  let component: InstallBootstrapPageComponent;
  let fixture: ComponentFixture<InstallBootstrapPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PagesModule, TestingModule, ToastrModule.forRoot(), TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallBootstrapPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
