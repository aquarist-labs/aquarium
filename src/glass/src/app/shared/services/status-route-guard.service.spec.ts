/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { StatusService } from '~/app/shared/services/api/status.service';
import { StatusRouteGuardService } from '~/app/shared/services/status-route-guard.service';

const fakeRouterStateSnapshot = (url: string): RouterStateSnapshot =>
  ({
    url
  } as RouterStateSnapshot);

describe('StatusRouteGuardService', () => {
  let service: StatusRouteGuardService;
  let statusService: StatusService;
  let router: Router;
  let httpTestingController: HttpTestingController;
  let urlTree: (url: string) => UrlTree;

  const activatedRouteSnapshot = {} as ActivatedRouteSnapshot;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [StatusRouteGuardService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    });

    service = TestBed.inject(StatusRouteGuardService);
    statusService = TestBed.inject(StatusService);
    router = TestBed.inject(Router);
    httpTestingController = TestBed.inject(HttpTestingController);

    urlTree = (url: string) => router.parseUrl(url);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should redirect', (done) => {
    const url = '/foo';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'none' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(urlTree('/installer'));
      done();
    });
  });

  it('should redirect with error', (done) => {
    const url = '/foo';
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
    httpTestingController
      .expectOne('api/status/')
      .error(new ErrorEvent('Unknown Error'), { status: 500 });
    httpTestingController.verify();
  });

  it('should not redirect [bootstrapping]', (done) => {
    const url = '/installer/create/bootstrap';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'bootstrapping' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
  });

  it('should redirect [bootstrapping]', (done) => {
    const url = '/installer/welcome';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'bootstrapping' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(urlTree('/installer/create/bootstrap'));
      done();
    });
  });

  it('should not redirect [bootstrapped]', (done) => {
    const url = '/installer/create/deployment';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'bootstrapped' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
  });

  it('should redirect [bootstrapped]', (done) => {
    const url = '/installer/welcome';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'bootstrapped' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(urlTree('/installer/create/deployment'));
      done();
    });
  });

  it('should redirect [ready]', (done) => {
    const url = '/bar';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'ready' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(urlTree('/dashboard'));
      done();
    });
  });

  it('should not redirect [none,1]', (done) => {
    const url = '/installer/welcome';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'none' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
  });

  it('should not redirect [none,2]', (done) => {
    const url = '/installer/install-mode';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'none' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
  });

  it('should not redirect [none,3]', (done) => {
    const url = '/installer/create/bootstrap';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'none' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
  });

  it('should redirect [none]', (done) => {
    const url = '/baz';
    spyOn(statusService, 'status').and.returnValue(of({ deployment_state: { stage: 'none' } }));
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(urlTree('/installer'));
      done();
    });
  });
});
