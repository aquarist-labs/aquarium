import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { CoreModule } from '~/app/core/core.module';
import { BreadcrumbsComponent } from '~/app/core/navigation-bar/breadcrumbs/breadcrumbs.component';
import { SharedModule } from '~/app/shared/shared.module';

describe('BreadcrumbsComponent', () => {
  let component: BreadcrumbsComponent;
  let fixture: ComponentFixture<BreadcrumbsComponent>;
  let activatedRouteRoot: ActivatedRoute;

  class ActivatedRootMock {
    get root() {
      return activatedRouteRoot;
    }
  }

  const mockRoute = ({
    breadcrumb,
    path,
    params,
    firstChild
  }: {
    breadcrumb?: string;
    path?: string;
    params?: { [name: string]: string };
    firstChild?: ActivatedRoute;
  }) => {
    let routeConfig;
    let snapshot;
    if (breadcrumb || path) {
      routeConfig = {
        path,
        data: {
          breadcrumb
        }
      };
    }
    if (params) {
      snapshot = { params };
    }
    // @ts-ignore
    return { routeConfig, snapshot, firstChild } as ActivatedRoute;
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoreModule, SharedModule, RouterTestingModule],
      providers: [
        {
          provide: ActivatedRoute,
          useClass: ActivatedRootMock
        }
      ]
    }).compileComponents();
  });

  const initializeComponent = () => {
    fixture = TestBed.createComponent(BreadcrumbsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  };

  beforeEach(() => {
    activatedRouteRoot = mockRoute({
      path: '',
      firstChild: mockRoute({
        breadcrumb: 'Dashboard',
        path: 'dashboard',
        firstChild: mockRoute({
          path: 'users',
          firstChild: mockRoute({ breadcrumb: 'Users', path: '' })
        })
      })
    });
  });

  it('should create', () => {
    initializeComponent();
    expect(component).toBeTruthy();
  });

  it('should test users page', () => {
    initializeComponent();
    expect(component.breadcrumbs).toEqual([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Users', path: '/dashboard/users' }
    ]);
  });

  it('should test users form editing a user', () => {
    // @ts-ignore
    activatedRouteRoot.firstChild?.firstChild?.firstChild?.firstChild = mockRoute({
      breadcrumb: 'Edit',
      path: 'edit/:name',
      params: {
        name: 'Leroy'
      }
    });
    initializeComponent();
    expect(component.breadcrumbs).toEqual([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Users', path: '/dashboard/users' },
      { label: 'Edit Leroy', path: '/dashboard/users/edit/Leroy' }
    ]);
  });
});
