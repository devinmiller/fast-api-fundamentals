from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
import uvicorn

from schemas import Car, CarInput


app = FastAPI(title="Car Sharing")

engine = create_engine(
    "sqlite:///carsharing.db",
    connect_args={"check_same_thread": False},
    echo=True
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/api/cars")
def get_cars(size: str | None = None, doors: int | None = None, session: Session = Depends(get_session)) -> list:
    query = select(Car)
    if size:
        query = query.where(Car.size == size)
    if doors:
        query = query.where(Car.doors == doors)

    return session.exec(query).all()


@app.get("/api/cars/{id}", response_model=Car)
def car_by_id(id: int, session: Session = Depends(get_session)) -> Car:
    car = session.get(Car, id)
    if car:
        return car
    else:
        raise HTTPException(status_code=404, detail=f"No car with id={id}.")


if __name__ == "__main__":
    uvicorn.run("carsharing:app", host="0.0.0.0", port=8000, reload=True)


@app.post("/api/cars", response_model=Car)
def add_car(car_input: CarInput, session: Session = Depends(get_session)) -> Car:
    new_car = Car.from_orm(car_input)
    session.add(new_car)
    session.commit()
    session.refresh(new_car)
    return new_car


@app.delete("/api/cars/{id}", status_code=204)
def remove_car(id: int, session: Session = Depends(get_session)) -> None:
    car = session.get(Car, id)

    if car:
        session.delete(car)
        session.commit()
    else:
        raise HTTPException(status_code=404, detail=f"No car with id={id}")


@app.put("/api/cars/{id}", response_model=Car)
def change_care(id: int, new_data: CarInput, session: Session = Depends(get_session)) -> Car:
    car = session.get(Car, id)

    if car:
        car.fuel = new_data.fuel
        car.transmission = new_data.transmission
        car.size = new_data.size
        car.doors = new_data.doors
        session.commit()
        return car
    else:
        raise HTTPException(status_code=404, detail=f"No car with id={id}")


# @app.post("/api/cars/{car_id}/trips", response_model=TripOutput)
# def add_trip(car_id: int, trip: TripInput) -> TripOutput:
#     matches = [car for car in db if car.id == car_id]

#     if matches:
#         car = matches[0]
#         new_trip = TripOutput(id=len(car.trips) + 1, **trip.model_dump())
#         car.trips.append(new_trip)
#         save_db(db)
#         return new_trip
#     else:
#         raise HTTPException(status_code=404, detail=f"No car with id={id}")
