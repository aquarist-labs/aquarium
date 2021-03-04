import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { ComponentsModule } from '~/app/shared/components/components.module';
import { DatatableComponent } from '~/app/shared/components/datatable/datatable.component';

describe('DatatableComponent', () => {
  let component: DatatableComponent;
  let fixture: ComponentFixture<DatatableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComponentsModule, NoopAnimationsModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DatatableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render cell', () => {
    const pipe = {
      transform: (value: any) => value
    };
    const pipeSpy = spyOn(pipe, 'transform').and.returnValue('bar');
    component.columns = [
      {
        name: 'Foo',
        prop: 'foo',
        pipe
      }
    ];
    expect(component.renderCellValue([{ foo: 'test' }], component.columns[0])).toBe('bar');
    expect(pipeSpy).toHaveBeenCalled();
  });
});
