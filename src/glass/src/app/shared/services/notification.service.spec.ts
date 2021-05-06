import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ToastrModule, ToastrService } from 'ngx-toastr';

import { NotificationService } from '~/app/shared/services/notification.service';
import { SharedModule } from '~/app/shared/shared.module';

describe('NotificationService', () => {
  let service: NotificationService;
  let toastrService: ToastrService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule, ToastrModule.forRoot()]
    });
    toastrService = TestBed.inject(ToastrService);
    service = TestBed.inject(NotificationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should show notification [1]', fakeAsync(() => {
    spyOn(toastrService, 'info');
    service.show('foo', { duration: 2000, type: 'info' });
    tick(5);
    expect(toastrService.info).toHaveBeenCalledWith('foo', undefined, {
      timeOut: 2000
    });
  }));

  it('should show notification [2]', fakeAsync(() => {
    spyOn(toastrService, 'info');
    service.show('bar');
    tick(5);
    expect(toastrService.info).toHaveBeenCalledWith('bar', undefined, {
      timeOut: 5000
    });
  }));

  it('should show notification [3]', fakeAsync(() => {
    spyOn(toastrService, 'error');
    service.show('baz', { type: 'error' });
    tick(5);
    expect(toastrService.error).toHaveBeenCalledWith('baz', undefined, {
      timeOut: 5000
    });
  }));
});
