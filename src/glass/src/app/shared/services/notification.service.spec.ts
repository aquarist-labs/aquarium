import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';

import { NotificationService } from '~/app/shared/services/notification.service';
import { SharedModule } from '~/app/shared/shared.module';

describe('NotificationService', () => {
  let service: NotificationService;
  const fakeSnackBar = {
    open: (message: string, action?: string, config?: Record<string, any>) => true
  };
  let snackBar: MatSnackBar;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule],
      providers: [
        {
          provide: MatSnackBar,
          useValue: fakeSnackBar
        }
      ]
    });
    snackBar = TestBed.inject(MatSnackBar);
    service = TestBed.inject(NotificationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should show notification [1]', fakeAsync(() => {
    spyOn(snackBar, 'open');
    service.show('foo', { duration: 5000, type: 'info' });
    tick(5);
    expect(snackBar.open).toHaveBeenCalledWith('foo', undefined, {
      duration: 5000,
      panelClass: undefined
    });
  }));

  it('should show notification [2]', fakeAsync(() => {
    spyOn(snackBar, 'open');
    service.show('bar');
    tick(5);
    expect(snackBar.open).toHaveBeenCalledWith('bar', undefined, {
      duration: 2000,
      panelClass: undefined
    });
  }));

  it('should show notification [3]', fakeAsync(() => {
    spyOn(snackBar, 'open');
    service.show('baz', { type: 'error' });
    tick(5);
    expect(snackBar.open).toHaveBeenCalledWith('baz', undefined, {
      duration: 2000,
      panelClass: 'glass-color-theme-error'
    });
  }));
});
