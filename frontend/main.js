initSqlJs().then(function (SQL) {
  async function getDB() {
    const response = await fetch("../cartalk.db");
    const arrayBuffer = await response.arrayBuffer();
    const uInt8Array = new Uint8Array(arrayBuffer);
    return uInt8Array;
  }

  // const uInt8Array = getDB();
  // // resolve the promise of the async function
  // const uInt8Array = await getDB();
  getDB().then((db_data) => {
    const db = new SQL.Database(db_data);

    const staff = db.exec("SELECT * FROM staff");
    console.log(staff);
    staff[0].values.forEach((row) => {
      const li = document.createElement("li");
      li.innerHTML = `${row[1]}`;
      document.querySelector("#staff").querySelector("ul").appendChild(li);
      li.addEventListener("click", () => {
        const text = row[2];
        console.log(text);
        document.querySelector("#text").innerHTML = `<b>${row[1]}</b></br></br>${row[2]}`;
      });
    });

    const puzzlers = db.exec("SELECT * FROM puzzlers");
    console.log(puzzlers);
    puzzlers[0].values.forEach((row) => {
      const li = document.createElement("li");
      li.innerHTML = `<i>${row[2]}</i> - ${row[1]}`;
      document.querySelector("#puzzlers").querySelector("ul").appendChild(li);
      li.addEventListener("click", () => {
        const text = row[3];
        console.log(text);
        document.querySelector("#text").innerHTML = `<b>${row[1]}</b><br/><br/>` + text.replaceAll(
          "\n",
          "<br/><br/>"
        );
      });
    });

    const letters = db.exec("SELECT * FROM letters");
    console.log(letters);
    letters[0].values.forEach((row) => {
      const li = document.createElement("li");
      li.innerHTML = `${row[1]}`;

      document.querySelector("#letters").querySelector("ul").appendChild(li);

      li.addEventListener("click", () => {
        const text = row[2];
        console.log(text);
        document.querySelector("#text").innerHTML = `<b>${row[1]}</b><br/><br/>` + text.replaceAll(
          "\n",
          "<br/><br/>"
        );
      });
    });
  });
});
