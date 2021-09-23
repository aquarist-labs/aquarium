/* eslint-disable max-len */
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule, ToastrService } from 'ngx-toastr';

import { InstallCreateWizardPageComponent } from '~/app/pages/install-wizard/install-create-wizard-page/install-create-wizard-page.component';
import { PagesModule } from '~/app/pages/pages.module';
import { HttpErrorInterceptorService } from '~/app/shared/services/http-error-interceptor.service';
import { TestingModule } from '~/app/testing.module';

describe('InstallCreateWizardPageComponent', () => {
  let component: InstallCreateWizardPageComponent;
  let fixture: ComponentFixture<InstallCreateWizardPageComponent>;
  let httpTesting: HttpTestingController;
  let toastrService: ToastrService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PagesModule, TestingModule, ToastrModule.forRoot(), TranslateModule.forRoot()],
      providers: [
        {
          provide: HTTP_INTERCEPTORS,
          useClass: HttpErrorInterceptorService,
          multi: true
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstallCreateWizardPageComponent);
    component = fixture.componentInstance;
    httpTesting = TestBed.inject(HttpTestingController);
    toastrService = TestBed.inject(ToastrService);
    jest.spyOn(toastrService, 'error');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show notification only once [1]', fakeAsync(() => {
    httpTesting
      .expectOne({ url: 'api/nodes/deployment/status', method: 'GET' })
      .error(new ErrorEvent('Unknown error'), { status: 500 });
    tick(5);
    expect(toastrService.error).toHaveBeenCalledTimes(1);
    flush();
  }));

  it('should show notification only once [2]', fakeAsync(() => {
    httpTesting
      .expectOne({ url: 'api/local/status', method: 'GET' })
      .error(new ErrorEvent('Unknown error'), { status: 500 });
    tick(5);
    expect(toastrService.error).toHaveBeenCalledTimes(1);
    flush();
  }));

  it('should show notification only once [3]', fakeAsync(() => {
    component.finishDeployment();
    httpTesting
      .match('api/nodes/deployment/finished')[0]
      .error(new ErrorEvent('Unknown error'), { status: 500 });
    tick(5);
    expect(toastrService.error).toHaveBeenCalledTimes(1);
    flush();
  }));
});
