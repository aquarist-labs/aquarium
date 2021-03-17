import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';

import { BootstrapPageComponent } from '~/app/pages/bootstrap-page/bootstrap-page.component';
import { PagesModule } from '~/app/pages/pages.module';
import { BootstrapService, BootstrapStageEnum } from '~/app/shared/services/api/bootstrap.service';
import { NotificationService } from '~/app/shared/services/notification.service';

describe('BootstrapPageComponent', () => {
  let component: BootstrapPageComponent;
  let fixture: ComponentFixture<BootstrapPageComponent>;
  let bootstrapService: BootstrapService;
  let notificationService: NotificationService;
  let httpTestingController: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [BootstrapService, NotificationService],
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        PagesModule,
        RouterTestingModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BootstrapPageComponent);
    component = fixture.componentInstance;
    bootstrapService = TestBed.inject(BootstrapService);
    notificationService = TestBed.inject(NotificationService);
    httpTestingController = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start bootstrapping', () => {
    spyOn(bootstrapService, 'start').and.returnValue(of({ success: true }));
    component.doBootstrap();
    expect(bootstrapService.start).toHaveBeenCalled();
    expect(component.bootstrapping).toBeTruthy();
    expect(component.blockUI.isActive).toBeTruthy();
  });

  it('should fail start bootstrapping', () => {
    spyOn(bootstrapService, 'start').and.returnValue(of({ success: false }));
    spyOn(notificationService, 'show').and.stub();
    component.doBootstrap();
    expect(bootstrapService.start).toHaveBeenCalled();
    expect(component.bootstrapping).toBeFalsy();
    expect(component.blockUI.isActive).toBeFalsy();
    expect(notificationService.show).toHaveBeenCalled();
  });

  it('should error bootstrapping', () => {
    component.doBootstrap();
    httpTestingController.expectOne('./assets/mdi.svg');
    httpTestingController.expectOne('api/bootstrap/status');
    httpTestingController
      .expectOne('api/bootstrap/start')
      .error(new ErrorEvent('Unknown Error'), { status: 404 });
    httpTestingController.verify();
    expect(component.bootstrapping).toBeFalsy();
    expect(component.blockUI.isActive).toBeFalsy();
  });

  it('should poll bootstrap [stage=done]', fakeAsync(() => {
    spyOn(router, 'navigate').and.stub();
    spyOn(bootstrapService, 'status').and.returnValue(of({ stage: BootstrapStageEnum.done }));
    component.pollBootstrapStatus();
    tick(5000);
    expect(bootstrapService.status).toHaveBeenCalledTimes(1);
    expect(component.blockUI.isActive).toBeFalsy();
    expect(router.navigate).toHaveBeenCalledWith(['/installer/create/deployment']);
  }));

  it('should poll bootstrap [stage=error]', fakeAsync(() => {
    spyOn(bootstrapService, 'status').and.returnValue(of({ stage: BootstrapStageEnum.error }));
    spyOn(notificationService, 'show').and.stub();
    component.pollBootstrapStatus();
    tick(5000);
    expect(bootstrapService.status).toHaveBeenCalledTimes(1);
    expect(component.bootstrapping).toBeFalsy();
    expect(component.blockUI.isActive).toBeFalsy();
    expect(notificationService.show).toHaveBeenCalledWith('Failed to bootstrap the system.', {
      type: 'error'
    });
  }));

  it('should poll bootstrap [stage=running,done]', fakeAsync(() => {
    httpTestingController.expectOne('./assets/mdi.svg');
    httpTestingController.expectOne('api/bootstrap/status');
    spyOn(router, 'navigate').and.stub();
    component.pollBootstrapStatus();
    tick(1);
    httpTestingController
      .expectOne('api/bootstrap/status')
      .flush({ stage: BootstrapStageEnum.running });
    tick(5000);
    httpTestingController
      .expectOne('api/bootstrap/status')
      .flush({ stage: BootstrapStageEnum.done });
    tick(5000);
    httpTestingController.expectNone('api/bootstrap/status');
    expect(component.blockUI.isActive).toBeFalsy();
    expect(router.navigate).toHaveBeenCalled();
    httpTestingController.verify();
  }));
});
