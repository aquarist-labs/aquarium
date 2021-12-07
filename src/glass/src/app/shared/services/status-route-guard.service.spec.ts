/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { StatusRouteGuardService } from '~/app/shared/services/status-route-guard.service';
import DoneCallback = jest.DoneCallback;
import {
  DeploymentErrorEnum,
  DeploymentStateEnum,
  DeployService,
  InitStateEnum
} from '~/app/shared/services/api/deploy.service';

const fakeRouterStateSnapshot = (url: string): RouterStateSnapshot =>
  ({
    url
  } as RouterStateSnapshot);

describe('StatusRouteGuardService', () => {
  let service: StatusRouteGuardService;
  let deployService: DeployService;
  let router: Router;
  let httpTestingController: HttpTestingController;
  let urlTree: (url: string) => UrlTree;

  const activatedRouteSnapshot = {} as ActivatedRouteSnapshot;

  const expectRouting = (
    url: string,
    init: InitStateEnum,
    deployment: DeploymentStateEnum,
    result: boolean | UrlTree,
    done: DoneCallback
  ) => {
    jest.spyOn(deployService, 'status').mockReturnValue(
      of({
        installed: false,
        status: { state: { init, deployment }, error: { code: DeploymentErrorEnum.none } }
      })
    );
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toEqual(result);
      done();
    });
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [StatusRouteGuardService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    });

    service = TestBed.inject(StatusRouteGuardService);
    deployService = TestBed.inject(DeployService);
    router = TestBed.inject(Router);
    httpTestingController = TestBed.inject(HttpTestingController);

    urlTree = (url: string) => router.parseUrl(url);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should redirect (1)', (done) => {
    expectRouting(
      '/foo',
      InitStateEnum.none,
      DeploymentStateEnum.none,
      urlTree('/installer/welcome'),
      done
    );
  });

  it('should redirect with error', (done) => {
    const url = '/foo';
    service.canActivate(activatedRouteSnapshot, fakeRouterStateSnapshot(url)).subscribe((res) => {
      expect(res).toBeTruthy();
      done();
    });
    httpTestingController
      .expectOne('api/deploy/status')
      .error(new ErrorEvent('Unknown Error'), { status: 500 });
    httpTestingController.verify();
  });

  it('should redirect (2)', (done) => {
    expectRouting(
      '/installer/welcome',
      InitStateEnum.installed,
      DeploymentStateEnum.deploying,
      urlTree('/installer/create'),
      done
    );
  });

  it('should redirect (3)', (done) => {
    expectRouting(
      '/bar',
      InitStateEnum.deployed,
      DeploymentStateEnum.deployed,
      urlTree('/dashboard'),
      done
    );
  });

  it('should redirect (5)', (done) => {
    expectRouting(
      '/baz',
      InitStateEnum.none,
      DeploymentStateEnum.none,
      urlTree('/installer/welcome'),
      done
    );
  });

  it('should not redirect (1)', (done) => {
    expectRouting(
      '/installer/create',
      InitStateEnum.installed,
      DeploymentStateEnum.none,
      true,
      done
    );
  });

  it('should not redirect (2)', (done) => {
    expectRouting('/dashboard', InitStateEnum.deployed, DeploymentStateEnum.deployed, true, done);
  });

  it('should not redirect (3)', (done) => {
    expectRouting(
      '/installer/install-mode',
      InitStateEnum.installed,
      DeploymentStateEnum.none,
      true,
      done
    );
  });

  it('should not redirect (4)', (done) => {
    expectRouting(
      '/installer/create',
      InitStateEnum.installed,
      DeploymentStateEnum.none,
      true,
      done
    );
  });

  it('should not redirect (5)', (done) => {
    expectRouting('/installer/join', InitStateEnum.installed, DeploymentStateEnum.none, true, done);
  });

  it('should not redirect (6)', (done) => {
    expectRouting('/installer/welcome', InitStateEnum.none, DeploymentStateEnum.none, true, done);
  });

  it('should not redirect (7)', (done) => {
    expectRouting('/installer/bootstrap', InitStateEnum.none, DeploymentStateEnum.none, true, done);
  });
});
