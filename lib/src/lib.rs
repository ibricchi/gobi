use std::ops::Deref;

pub mod file;
pub mod recipes;

#[derive(Debug, Clone)]
pub struct GobiError {
    pub code: i32,
    pub msg: String,
}

impl GobiError {
    pub fn merge(self, other: GobiError) -> GobiError {
        GobiError {
            code: if self.code == other.code {
                self.code
            } else {
                1
            },
            msg: format!("{}\n{}", self.msg, other.msg),
        }
    }
}

impl Default for GobiError {
    fn default() -> GobiError {
        GobiError {
            code: 0,
            msg: String::new(),
        }
    }
}

pub type GobiResult<T> = Result<T, GobiError>;

struct GobiResultIterator<I> {
    iter: I,
}

impl<I, T> From<I> for GobiResultIterator<I>
where
    I: Iterator<Item = GobiResult<T>>,
{
    fn from(iter: I) -> Self {
        GobiResultIterator { iter }
    }
}

impl<I> Deref for GobiResultIterator<I> {
    type Target = I;

    fn deref(&self) -> &Self::Target {
        &self.iter
    }
}

impl<I, T> GobiResultIterator<I>
where
    I: Iterator<Item = GobiResult<T>>,
{
    fn try_collect<G>(self) -> GobiResult<G>
    where
        Self: Sized,
        G: Default + Extend<T>,
    {
        let (res, err) = self.iter.fold(
            (G::default(), GobiError::default()),
            |(mut g, err), val| match val {
                Ok(val) => {
                    g.extend(vec![val].into_iter());
                    (g, err)
                }
                Err(e) => (g, err.merge(e)),
            },
        );
        if err.code != 0 {
            Err(err)
        } else {
            Ok(res)
        }
    }
}
