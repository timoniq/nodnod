<img src="/.github/logo.png" width="150px">

# NodNod

🧑‍🧑‍🧒‍🧒 Programming in Python enhanced with Nodes

[![codecov](https://codecov.io/gh/timoniq/nodnod/branch/dev/graph/badge.svg)](https://codecov.io/gh/timoniq/nodnod)
[![pypi](https://img.shields.io/pypi/v/nodnod.svg?labelColor=black&style=flat-square&logo=pypi)](https://pypi.org/project/nodnod)

nodnod is a dependency injection tool

nodnod strives to be effective and simple: it has many agents, but, for example, asyncio agent turns each dependency into a coroutine and yields decomposed dependency net to your loop to solve it the best way possible

nodnod is easy to integrate, be it a framework or a small project

nodnod provides many interfaces to build different kinds of dependencies:

* **polymorphic** - node whose resolution may vary

  ```python
  @polymorphic[Face]
  class DetectedFace:
      @case
      def from_video(cls, video: Video) -> Face:
          x, y = detect_face(video.frames[0]).expect(ComposeError("No face"))
          return Face(x, y)

      @case
      def from_photo(cls, photo: Photo) -> Face:
          ...
  ```

* **scalar** node disguises as its result for type checkers
  ```python
  @scalar_node
  class Username:
      @classmethod
      def __compose__(cls, user: User) -> str:
          return user.username.map_error(lambda _: f"#{user.id}")
  ```

* **logical or**
  ```python
  @classmethod
  def __compose__(cls, dep: One | Another) -> ...: ...
  ```
  * can be concurrent: two nodes are racing to deliver their resolution
  * or sequential: if first resolution fails, next one is triggered

* **kungfu funtional types** are supported:
  
  Exceptions can be intercepted:

  ```python
  @classmethod
  def __compose__(cls, weather: Result[Weather, ConnectionError)): ...
  ```

  Dependencies can be optional:

  ```python
  @classmethod
  def __compose__(cls, face: Option[DetectedFace]): ...
  ```

your contributions are welcome!

🌺
