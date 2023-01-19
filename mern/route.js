const express = require("express");
const products = require("./products");

const router = express.Router();

router.get("/", async (req, res) => {
  try {
    const prod= await products.find();
    console.log(prod)

    res.status(200).send(prod);
  } catch {
    res.status(400);
  }
});

router.post("/", async (req, res) => {
    const product = req.body;
    console.log(product);
  try {
    const isUnique = !(await products.exists({ name: product.name }));
    if (isUnique) {
      const newProduct = (await products.create(product)).toJSON();
      return res.send(newProduct);
    } else return res.status(400).send("Product already exists");
  } catch (e) {
    console.error(e);
    return res.status(400).send(e);
  }
});

router.put("/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const newData = req.body;
    console.log(newData)
    try {
      const data = await products.findById(id);
      if (!!data) {
        const updateResult = (
          await products.findOneAndUpdate({ name: data.name }, newData, {
            new: true,
          })
        )?.toJSON();
        return res.send(updateResult);
      } else
        return res
          .status(404)
          .send("There is no document in the db with provided id");
    } catch {
      return res.status(400).send("something goes wrong");
    }
  } catch (e) {
    console.error(e);
    return res.status(404).send(e);
  }
});

router.delete("/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const data = await products.findById(id);
    if (!!data) {
      const deletedData = (
        await products.findOneAndDelete({
          _id: id,
        })
      )?.toJSON();
      return res.send(deletedData);
    } else return res.status(404).send("dokument with this id not found");
  } catch (e) {
    console.error(e);
    return res.status(400).send(e);
  }
});

router.get("/raport", async (req, res) => {
  try {
    const raport = await products.aggregate([
      {
        $project: {
          name: 1,
          amount: 1,
          totalValue: { $multiply: ["$amount", "$price"] },
        },
      },
    ]);
    console.log(raport)
    return res.send(raport);
  } catch (e) {
    console.error(e);
    return res.status(400).send(e);
  }
});

module.exports = router;
